import os
import time
from typing import Dict, Any
from datetime import datetime
from loguru import logger


class ReportGenerator:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.template_path = os.path.join(os.path.dirname(__file__), "..", template_dir, "performance_report.html")
        
    def generate_html_report(self, analysis_data: Dict[str, Any], 
                         device_info: str = "Unknown Device",
                         app_info: str = "Unknown App") -> Dict[str, Any]:
        try:
            if not analysis_data:
                raise ValueError("性能分析数据为空，无法生成报告")
            
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            html_content = self._fill_template(template, analysis_data, device_info, app_info)
            
            return {
                'success': True,
                'html_content': html_content,
                'message': '报告生成成功'
            }
            
        except FileNotFoundError as e:
            logger.error(f"Template file not found: {self.template_path}")
            return {
                'success': False,
                'error_type': 'template_not_found',
                'message': f'报告模板文件未找到: {str(e)}',
                'details': '请检查 templates 目录是否存在 performance_report.html 文件'
            }
        except ValueError as e:
            logger.error(f"Invalid analysis data: {e}")
            return {
                'success': False,
                'error_type': 'invalid_data',
                'message': f'性能数据无效: {str(e)}',
                'details': '请确保已收集足够的性能数据后再生成报告'
            }
        except KeyError as e:
            logger.error(f"Missing required field in analysis data: {e}")
            return {
                'success': False,
                'error_type': 'missing_field',
                'message': f'缺少必要的数据字段: {str(e)}',
                'details': '性能分析数据不完整，请重新收集数据'
            }
        except Exception as e:
            logger.error(f"Unexpected error generating HTML report: {e}")
            return {
                'success': False,
                'error_type': 'unknown_error',
                'message': f'报告生成失败: {str(e)}',
                'details': '发生未知错误，请稍后重试'
            }
    
    def _fill_template(self, template: str, analysis_data: Dict[str, Any],
                     device_info: str, app_info: str) -> str:
        fps = analysis_data.get('fps', {})
        memory = analysis_data.get('memory', {})
        cpu = analysis_data.get('cpu', {})
        gpu = analysis_data.get('gpu', {})
        battery_temp = analysis_data.get('battery_temp', {})
        
        overall_score = analysis_data.get('overall_score', 0)
        overall_score_class = self._get_score_class(overall_score)
        
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        replacements = {
            '{{report_time}}': report_time,
            '{{device_info}}': device_info,
            '{{app_info}}': app_info,
            '{{overall_score}}': str(overall_score),
            '{{overall_score_class}}': overall_score_class,
            
            '{{fps_stability_class}}': self._get_level_class(fps.get('stability_level', 'unknown')),
            '{{fps_stability_text}}': self._get_level_text(fps.get('stability_level', 'unknown')),
            '{{fps_avg}}': str(fps.get('fps_avg', 0)),
            '{{fps_min}}': str(fps.get('fps_min', 0)),
            '{{fps_max}}': str(fps.get('fps_max', 0)),
            '{{fps_std}}': str(fps.get('fps_std', 0)),
            '{{jank_rate}}': str(fps.get('jank_rate', 0)),
            '{{jank_rate_warning}}': 'warning' if fps.get('jank_rate', 0) > 5 else '',
            '{{big_jank_count}}': str(fps.get('big_jank_count', 0)),
            '{{big_jank_warning}}': 'warning' if fps.get('big_jank_count', 0) > 0 else '',
            
            '{{leak_risk_class}}': self._get_risk_class(memory.get('leak_risk', 'low')),
            '{{leak_risk_text}}': self._get_risk_text(memory.get('leak_risk', 'low')),
            '{{memory_current}}': str(memory.get('memory_current', 0)),
            '{{memory_avg}}': str(memory.get('memory_avg', 0)),
            '{{memory_max}}': str(memory.get('memory_max', 0)),
            '{{memory_trend_icon}}': self._get_trend_icon(memory.get('memory_trend', 'stable')),
            '{{memory_trend_text}}': self._get_trend_text(memory.get('memory_trend', 'stable')),
            '{{spike_warning}}': 'warning' if memory.get('memory_spike_count', 0) > 3 else '',
            '{{memory_spike_count}}': str(memory.get('memory_spike_count', 0)),
            
            '{{thermal_risk_class}}': self._get_risk_class(battery_temp.get('thermal_throttle_risk', 'low')),
            '{{thermal_risk_text}}': self._get_risk_text(battery_temp.get('thermal_throttle_risk', 'low')),
            '{{temp_current}}': str(battery_temp.get('temp_current', 0)),
            '{{temp_avg}}': str(battery_temp.get('temp_avg', 0)),
            '{{temp_min}}': str(battery_temp.get('temp_min', 0)),
            '{{temp_max}}': str(battery_temp.get('temp_max', 0)),
            '{{temp_trend_icon}}': self._get_trend_icon(battery_temp.get('temp_trend', 'stable')),
            '{{temp_trend_text}}': self._get_trend_text(battery_temp.get('temp_trend', 'stable')),
            '{{temp_warning}}': 'warning' if battery_temp.get('temp_current', 0) > 40 else '',
            
            '{{cpu_current}}': str(cpu.get('cpu_current', 0)),
            '{{cpu_avg}}': str(cpu.get('cpu_avg', 0)),
            '{{cpu_min}}': str(cpu.get('cpu_min', 0)),
            '{{cpu_max}}': str(cpu.get('cpu_max', 0)),
            '{{cpu_trend_icon}}': self._get_trend_icon(cpu.get('cpu_trend', 'stable')),
            '{{cpu_trend_text}}': self._get_trend_text(cpu.get('cpu_trend', 'stable')),
            '{{cpu_warning}}': 'warning' if cpu.get('cpu_current', 0) > 70 else '',
            
            '{{gpu_current}}': str(gpu.get('gpu_current', 0)),
            '{{gpu_avg}}': str(gpu.get('gpu_avg', 0)),
            '{{gpu_min}}': str(gpu.get('gpu_min', 0)),
            '{{gpu_max}}': str(gpu.get('gpu_max', 0)),
            '{{gpu_trend_icon}}': self._get_trend_icon(gpu.get('gpu_trend', 'stable')),
            '{{gpu_trend_text}}': self._get_trend_text(gpu.get('gpu_trend', 'stable')),
            '{{gpu_warning}}': 'warning' if gpu.get('gpu_current', 0) > 70 else '',
            
            '{{recommendations_list}}': self._generate_recommendations_html(
                analysis_data.get('recommendations', [])
            )
        }
        
        html_content = template
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)
        
        return html_content
    
    def _get_score_class(self, score: float) -> str:
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'
    
    def _get_level_class(self, level: str) -> str:
        level_map = {
            'excellent': 'level-excellent',
            'good': 'level-good',
            'fair': 'level-fair',
            'poor': 'level-poor'
        }
        return level_map.get(level, 'level-unknown')
    
    def _get_level_text(self, level: str) -> str:
        text_map = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差'
        }
        return text_map.get(level, '未知')
    
    def _get_risk_class(self, risk: str) -> str:
        risk_map = {
            'high': 'level-poor',
            'medium': 'level-fair',
            'low': 'level-excellent'
        }
        return risk_map.get(risk, 'level-unknown')
    
    def _get_risk_text(self, risk: str) -> str:
        text_map = {
            'high': '高风险',
            'medium': '中等风险',
            'low': '低风险'
        }
        return text_map.get(risk, '未知')
    
    def _get_trend_icon(self, trend: str) -> str:
        icon_map = {
            'increasing_fast': '📈',
            'increasing': '📊',
            'stable': '➡️',
            'decreasing': '📉',
            'decreasing_fast': '⬇️'
        }
        return icon_map.get(trend, '➡️')
    
    def _get_trend_text(self, trend: str) -> str:
        text_map = {
            'increasing_fast': '快速上升',
            'increasing': '上升',
            'stable': '稳定',
            'decreasing': '下降',
            'decreasing_fast': '快速下降'
        }
        return text_map.get(trend, '稳定')
    
    def _generate_recommendations_html(self, recommendations: list) -> str:
        if not recommendations:
            return '<div class="recommendation-item">暂无明显优化建议</div>'
        
        html_items = []
        for rec in recommendations:
            html_items.append(f'<div class="recommendation-item">{rec}</div>')
        
        return '\n'.join(html_items)
    
    def save_report(self, html_content: str, output_dir: str = "reports", 
                   filename: str = None) -> Dict[str, Any]:
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"performance_report_{timestamp}.html"
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Report saved to: {filepath}")
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'message': '报告保存成功'
            }
            
        except PermissionError as e:
            logger.error(f"Permission denied when saving report: {e}")
            return {
                'success': False,
                'error_type': 'permission_error',
                'message': '没有保存权限',
                'details': f'无法写入文件 {output_dir}，请检查目录权限'
            }
        except OSError as e:
            logger.error(f"OS error saving report: {e}")
            return {
                'success': False,
                'error_type': 'os_error',
                'message': '文件系统错误',
                'details': f'保存文件时发生错误: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error saving report: {e}")
            return {
                'success': False,
                'error_type': 'unknown_error',
                'message': '保存报告失败',
                'details': f'发生未知错误: {str(e)}'
            }
