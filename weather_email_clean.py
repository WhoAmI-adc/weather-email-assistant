# -*- coding: utf-8 -*-
"""
小麻雀天气助手 - 免费邮件天气通知系统（含AQI空气质量）
使用Gmail、QQ邮箱等免费邮箱服务发送天气邮件
"""
import requests
import schedule
import time
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging
import random
import pytz

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherEmail:
    def __init__(self, config_file='email_config.json'):
        """初始化天气邮件服务"""
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"配置文件 {config_file} 不存在")
            return {}
    
    def get_weather(self, city_code=None):
        """获取天气信息"""
        city_code = city_code or self.config.get('city_code', '101010100')  # 默认北京
        weather_key = self.config.get('weather_api_key')
        
        if not weather_key:
            logger.error("未配置天气API密钥")
            return None
            
        # 使用和风天气API
        api_host = self.config.get('weather_api_host', 'devapi.qweather.com')
        url = f"https://{api_host}/v7/weather/now"
        params = {
            'location': city_code,
            'key': weather_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == '200':
                weather_info = data['now']
                
                # 获取未来3天预报
                forecast_url = f"https://{api_host}/v7/weather/3d"
                forecast_response = requests.get(forecast_url, params=params, timeout=10)
                forecast_data = forecast_response.json()
                
                # 获取空气质量数据
                air_quality = None
                try:
                    air_url = f"https://{api_host}/v7/air/now"
                    air_response = requests.get(air_url, params=params, timeout=10)
                    air_data = air_response.json()
                    if air_data.get('code') == '200':
                        air_quality = air_data.get('now', {})
                        logger.info("空气质量数据获取成功")
                    else:
                        logger.warning(f"获取空气质量失败: {air_data.get('code')}")
                except Exception as e:
                    logger.warning(f"获取空气质量异常: {e}")
                
                return {
                    'current': weather_info,
                    'forecast': forecast_data.get('daily', [])[:3] if forecast_data.get('code') == '200' else [],
                    'air_quality': air_quality
                }
            else:
                logger.error(f"获取天气失败: {data.get('code')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求天气API失败: {e}")
            return None
    
    def get_aqi_level(self, aqi_value):
        """根据AQI值获取等级描述"""
        if aqi_value is None:
            return "未知", "#999999"
        
        aqi = int(aqi_value)
        if aqi <= 50:
            return "优", "#00e400"
        elif aqi <= 100:
            return "良", "#ffff00"
        elif aqi <= 150:
            return "轻度污染", "#ff7e00"
        elif aqi <= 200:
            return "中度污染", "#ff0000"
        elif aqi <= 300:
            return "重度污染", "#8f3f97"
        else:
            return "严重污染", "#7e0023"
    
    def get_clothing_advice(self, weather_data):
        """根据天气生成智能穿衣建议"""
        if not weather_data:
            return ["天气信息不可用，请根据实际情况穿衣"]
        
        current = weather_data['current']
        temp = int(current.get('temp', 20))  # 当前温度
        weather_text = current.get('text', '').lower()  # 天气状况
        humidity = int(current.get('humidity', 50))  # 湿度
        wind_scale = current.get('windScale', '0')  # 风力等级
        
        # 获取明日温度范围（如果有预报）
        tomorrow_min = tomorrow_max = None
        if weather_data['forecast']:
            tomorrow = weather_data['forecast'][0]
            tomorrow_min = int(tomorrow.get('tempMin', temp))
            tomorrow_max = int(tomorrow.get('tempMax', temp))
        
        advice_list = []
        
        # 基础温度建议
        if temp <= 0:
            advice_list.append("🧥 建议穿厚羽绒服、棉衣，做好防寒保暖")
            advice_list.append("🧤 记得戴帽子、手套、围巾")
        elif temp <= 10:
            advice_list.append("🧥 建议穿厚外套、毛衣或薄羽绒服")
            advice_list.append("👖 可以穿厚裤子或加绒裤")
        elif temp <= 15:
            advice_list.append("🧥 建议穿薄外套、卫衣或针织衫")
            advice_list.append("👕 里面可以穿长袖T恤")
        elif temp <= 20:
            advice_list.append("👕 建议穿长袖衬衫、薄毛衣或薄外套")
            advice_list.append("👖 可以穿长裤或薄款休闲裤")
        elif temp <= 25:
            advice_list.append("👕 建议穿长袖T恤、衬衫或薄外套")
            advice_list.append("☀️ 温度适宜，注意适当增减衣物")
        elif temp <= 30:
            advice_list.append("👕 建议穿短袖T恤、衬衫或薄款上衣")
            advice_list.append("🩳 可以穿短裤、薄款长裤或裙子")
        else:
            advice_list.append("👕 建议穿清爽的短袖、薄款衣物")
            advice_list.append("🌡️ 天气较热，选择透气性好的衣物")
        
        # 特殊天气建议
        if '雨' in weather_text or '雷' in weather_text:
            advice_list.append("☔ 记得带雨伞，选择防水外套")
            advice_list.append("👟 建议穿防滑鞋，避免穿容易湿透的鞋子")
        elif '雪' in weather_text:
            advice_list.append("❄️ 雪天路滑，穿防滑保暖的鞋子")
            advice_list.append("🧥 选择防风防水的外套")
        elif '风' in weather_text or int(wind_scale) >= 4:
            advice_list.append("💨 风力较大，选择贴身不易被风吹起的衣物")
            advice_list.append("🧢 户外活动时注意固定帽子等配饰")
        elif '晴' in weather_text or '阳' in weather_text:
            advice_list.append("☀️ 晴天阳光强，建议做好防晒措施")
            advice_list.append("🕶️ 可以准备太阳镜和防晒霜")
        elif '雾' in weather_text or '霾' in weather_text:
            advice_list.append("😷 雾霾天气，建议佩戴口罩")
            advice_list.append("🚗 能见度低，出行注意安全")
        
        # 湿度建议
        if humidity >= 80:
            advice_list.append("💧 湿度较高，选择透气吸汗的材质")
        elif humidity <= 30:
            advice_list.append("💧 空气干燥，注意补水和润肤")
        
        # 温差建议
        if tomorrow_min is not None and tomorrow_max is not None:
            temp_diff = tomorrow_max - tomorrow_min
            if temp_diff >= 15:
                advice_list.append("🌡️ 昼夜温差大，建议洋葱式穿搭，方便增减")
            elif abs(temp - tomorrow_min) >= 10 or abs(temp - tomorrow_max) >= 10:
                advice_list.append("📈 气温变化较大，建议准备备用衣物")
        
        # AQI空气质量建议
        if weather_data.get('air_quality'):
            aqi_value = weather_data['air_quality'].get('aqi')
            if aqi_value:
                aqi = int(aqi_value)
                if aqi > 100:
                    advice_list.append("😷 空气质量较差，建议佩戴口罩")
                if aqi > 150:
                    advice_list.append("🏠 空气污染严重，减少户外活动")
                elif aqi <= 50:
                    advice_list.append("🫁 空气质量优良，适合户外活动")
        
        # 随机添加一些贴心提醒
        tips = [
            "💝 和huhu一样无忧无虑",
            "🌈 每天都要开开心心哒",
            "💪 今天也要努力！",
            "🎯 愿你每一天都很美好",
            "✨ 小麻雀生活愉快"
        ]
        # 使用北京时间判断是否为月初
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_now = datetime.now(beijing_tz)
        if beijing_now.day == 1:
            advice_list.append(f"{beijing_now.month}月快乐！黄雨珏同学！")
        else:
            advice_list.append(random.choice(tips))
            
        return advice_list
    
    def check_rain_alert(self, weather_data):
        """检查今天是否可能下雨"""
        if not weather_data or not weather_data['forecast']:
            return None
        
        # 检查当前天气是否有雨
        current = weather_data['current']
        current_text = current.get('text', '').lower()
        if any(keyword in current_text for keyword in ['雨', '雷', '阵雨', '毛毛雨', '小雨', '中雨', '大雨', '暴雨']):
            return "☔ 当前正在下雨，出门记得带伞！"
        
        # 检查今天是否可能下雨
        if weather_data['forecast']:
            today = weather_data['forecast'][0]
            day_text = today.get('textDay', '').lower()
            night_text = today.get('textNight', '').lower()
            
            # 检查今天白天或夜间是否有雨
            if (any(keyword in day_text for keyword in ['雨', '雷', '阵雨', '毛毛雨', '小雨', '中雨', '大雨', '暴雨']) or
                any(keyword in night_text for keyword in ['雨', '雷', '阵雨', '毛毛雨', '小雨', '中雨', '大雨', '暴雨'])):
                return "🌧️ 今天可能有雨，建议携带雨具"
        
        return None
    
    def format_weather_html(self, weather_data):
        """格式化天气信息为HTML邮件内容"""
        if not weather_data:
            return "<p>获取天气信息失败</p>"
            
        current = weather_data['current']
        
        # 检查雨天信息
        rain_alert = self.check_rain_alert(weather_data)
        
        # 获取AQI信息
        aqi_info = ""
        if weather_data.get('air_quality'):
            aqi_value = weather_data['air_quality'].get('aqi')
            if aqi_value:
                aqi_level, aqi_color = self.get_aqi_level(aqi_value)
                aqi_info = f'🫁 AQI {aqi_value} ({aqi_level}) | '
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .weather-card {{ 
                    background: linear-gradient(135deg, #74b9ff, #0984e3);
                    color: white; 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin: 10px 0;
                }}
                .current-weather {{ 
                    text-align: center; 
                    font-size: 1.2em; 
                }}
                .forecast {{ 
                    margin-top: 20px; 
                    background: #f8f9fa; 
                    color: #333; 
                    padding: 15px; 
                    border-radius: 8px;
                }}
                .forecast-item {{ 
                    padding: 8px; 
                    border-bottom: 1px solid #e9ecef;
                }}
                .rain-alert {{
                    background: linear-gradient(135deg, #74b9ff, #0984e3);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                    border-left: 4px solid #0066cc;
                    text-align: center;
                    font-size: 1.1em;
                }}
                .temperature {{ font-size: 2em; font-weight: bold; }}
                .date {{ color: #6c757d; font-size: 0.9em; }}
                .clothing-advice {{
                    background: linear-gradient(135deg, #fd79a8, #e84393);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <h1>小麻雀天气助手</h1>
            <div class="date">{datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日 %A')}</div>
            
            <div class="weather-card">
                <div class="current-weather">
                    <div class="temperature">{current.get('temp', 'N/A')}°C</div>
                    <div style="font-size: 1.1em; margin: 10px 0;">
                        {current.get('text', '未知')}
                    </div>
                    <div style="font-size: 0.9em;">
                        💨 {current.get('windDir', 'N/A')} {current.get('windScale', 'N/A')}级 | 
                        💧 湿度 {current.get('humidity', 'N/A')}% | 
                        {aqi_info}👁️ 能见度 {current.get('vis', 'N/A')}km
                    </div>
                </div>
            </div>
        """
        
        # 添加简单的降雨提醒
        if rain_alert:
            html += f'''
            <div class="rain-alert">
                {rain_alert}
            </div>
            '''
        
        # 添加预报信息
        if weather_data['forecast']:
            html += '<div class="forecast"><h3>📅 未来几天预报</h3>'
            weekdays = ['一', '二', '三', '四', '五', '六', '日']
            
            # 跳过今天，显示明天、后天和第三天
            for i, day in enumerate(weather_data['forecast'][1:], 1):  # 从索引1开始，跳过今天
                date_str = day.get('fxDate', '')
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        weekday = weekdays[date_obj.weekday()]
                        if i == 1:
                            day_label = "明天"
                        elif i == 2:
                            day_label = "后天"
                        elif i == 3:
                            day_label = f"周{weekday}"
                        else:
                            day_label = f"周{weekday}"
                    except:
                        day_label = f"第{i+1}天"
                else:
                    day_label = f"第{i+1}天"
                    
                html += f'''
                <div class="forecast-item">
                    <strong>{day_label}</strong> ({date_str})
                    <br>
                    🌅 白天: {day.get('textDay', 'N/A')} | 🌙 夜间: {day.get('textNight', 'N/A')}
                    <br>
                    🌡️ {day.get('tempMin', 'N/A')}°C ~ {day.get('tempMax', 'N/A')}°C | 
                    💨 {day.get('windDirDay', 'N/A')} {day.get('windScaleDay', 'N/A')}级
                </div>
                '''
                # 显示三天：明天、后天和第三天
                if i >= 3:
                    break
            
            html += '</div>'
        
        # 添加温馨提醒
        clothing_advice = self.get_clothing_advice(weather_data)
        if clothing_advice:
            html += '<div class="clothing-advice">'
            html += '<h3>💝 温馨提醒</h3>'
            for advice in clothing_advice:
                html += f'<div style="margin: 5px 0;">• {advice}</div>'
            html += '</div>'
        
        html += '''
            <hr style="margin: 20px 0;">
            <p style="color: #6c757d; font-size: 0.9em; text-align: center;">
                本邮件由小麻雀天气助手自动发送 🐦 | 数据来源：和风天气
            </p>
        </body>
        </html>
        '''
        
        return html
    
    def send_email(self, to_emails, subject, html_content):
        """发送邮件"""
        smtp_server = self.config.get('smtp_server')
        smtp_port = self.config.get('smtp_port', 587)
        email_user = self.config.get('email_user')
        email_password = self.config.get('email_password')
        
        if not all([smtp_server, email_user, email_password]):
            logger.error("邮箱配置不完整")
            return False
        
        success_count = 0
        
        # 为每个收件人单独发送邮件
        for email in to_emails:
            try:
                # 为每个收件人建立独立的SMTP连接
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()  # 启用TLS加密
                server.login(email_user, email_password)
                
                # 创建邮件
                msg = MIMEMultipart('alternative')
                
                # QQ邮箱要求From字段必须是登录邮箱
                msg['From'] = email_user
                msg['To'] = email
                msg['Subject'] = Header(subject, 'utf-8')
                
                # 添加HTML内容
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                text = msg.as_string()
                server.sendmail(email_user, [email], text)
                server.quit()
                
                logger.info(f"邮件发送成功: {email}")
                success_count += 1
                
                # 在发送间隔之间稍作停顿，避免被服务器限制
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"发送到 {email} 失败: {e}")
                try:
                    server.quit()
                except:
                    pass
        
        return success_count > 0
    
    def send_weather_email(self):
        """发送天气邮件"""
        logger.info("开始发送天气邮件...")
        
        # 获取天气信息
        weather_data = self.get_weather()
        
        if not weather_data:
            logger.error("获取天气信息失败，取消发送")
            return
        
        # 格式化邮件内容
        html_content = self.format_weather_html(weather_data)
        
        # 获取收件人列表
        recipients = self.config.get('recipients', [])
        if not recipients:
            logger.warning("没有配置邮件接收人")
            return
        
        # 生成邮件主题
        current = weather_data['current']
        subject = f"🐦 小麻雀天气助手：{current.get('text', '未知')} {current.get('temp', 'N/A')}°C"
        
        # 发送邮件
        success = self.send_email(recipients, subject, html_content)
        
        if success:
            logger.info("天气邮件发送完成")
        else:
            logger.error("天气邮件发送失败")
    
    def start_scheduler(self):
        """启动定时任务"""
        # 从配置文件读取发送时间
        send_times = self.config.get('send_times', ['09:00'])
        
        for send_time in send_times:
            schedule.every().day.at(send_time).do(self.send_weather_email)
            logger.info(f"已设置定时任务：每天 {send_time} 发送天气邮件")
        
        logger.info("定时任务启动，按Ctrl+C停止...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("程序已停止")

def main():
    """主函数"""
    weather_email = WeatherEmail()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # 测试模式：立即发送一次
        weather_email.send_weather_email()
    else:
        # 正常模式：启动定时任务
        weather_email.start_scheduler()

if __name__ == "__main__":
    main()
