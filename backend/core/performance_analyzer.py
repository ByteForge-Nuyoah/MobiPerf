from typing import Dict, List, Any, Optional
from collections import deque
from loguru import logger
import numpy as np


class PerformanceAnalyzer:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.fps_history = deque(maxlen=window_size)
        self.memory_history = deque(maxlen=window_size)
        self.cpu_history = deque(maxlen=window_size)
        self.jank_history = deque(maxlen=window_size)
        self.gpu_history = deque(maxlen=window_size)
        self.battery_temp_history = deque(maxlen=window_size)
        self.data_count = 0
        
    def add_metrics(self, metrics: Dict[str, Any]):
        timestamp = metrics.get('timestamp', 0)
        self.fps_history.append((timestamp, metrics.get('fps', 0)))
        self.memory_history.append((timestamp, metrics.get('memory', 0)))
        self.cpu_history.append((timestamp, metrics.get('cpu', 0)))
        self.jank_history.append((timestamp, metrics.get('jank', 0)))
        self.gpu_history.append((timestamp, metrics.get('gpu', 0)))
        self.battery_temp_history.append((timestamp, metrics.get('battery', {}).get('temp', 0)))
        self.data_count += 1
        
    def analyze_fps_stability(self) -> Dict[str, Any]:
        if len(self.fps_history) < 5:
            return {
                'fps_avg': 0,
                'fps_min': 0,
                'fps_max': 0,
                'fps_std': 0,
                'fps_variance': 0,
                'jank_rate': 0,
                'stutter_rate': 0,
                'big_jank_count': 0,
                'stability_score': 0,
                'stability_level': 'unknown'
            }
        
        fps_values = [fps for _, fps in self.fps_history]
        jank_values = [jank for _, jank in self.jank_history]
        
        fps_array = np.array(fps_values)
        jank_array = np.array(jank_values)
        
        fps_avg = float(np.mean(fps_array))
        fps_min = float(np.min(fps_array))
        fps_max = float(np.max(fps_array))
        fps_std = float(np.std(fps_array))
        fps_variance = float(np.var(fps_array))
        
        total_frames = np.sum(fps_array)
        total_jank = np.sum(jank_array)
        jank_rate = (total_jank / total_frames * 100) if total_frames > 0 else 0
        
        stutter_frames = np.sum(fps_array < 24)
        stutter_rate = (stutter_frames / len(fps_array) * 100) if len(fps_array) > 0 else 0
        
        big_jank_count = np.sum(jank_array > 2)
        
        stability_score = self._calculate_stability_score(
            fps_avg, fps_std, jank_rate, stutter_rate, big_jank_count
        )
        
        stability_level = self._get_stability_level(stability_score)
        
        return {
            'fps_avg': round(fps_avg, 2),
            'fps_min': round(fps_min, 2),
            'fps_max': round(fps_max, 2),
            'fps_std': round(fps_std, 2),
            'fps_variance': round(fps_variance, 2),
            'jank_rate': round(jank_rate, 2),
            'stutter_rate': round(stutter_rate, 2),
            'big_jank_count': int(big_jank_count),
            'stability_score': round(stability_score, 1),
            'stability_level': stability_level
        }
    
    def analyze_memory_trend(self) -> Dict[str, Any]:
        if len(self.memory_history) < 5:
            return {
                'memory_avg': 0,
                'memory_min': 0,
                'memory_max': 0,
                'memory_current': 0,
                'memory_growth_rate': 0,
                'memory_trend': 'stable',
                'leak_risk': 'low',
                'memory_spike_count': 0
            }
        
        memory_values = [mem for _, mem in self.memory_history]
        timestamps = [ts for ts, _ in self.memory_history]
        
        mem_array = np.array(memory_values)
        
        memory_avg = float(np.mean(mem_array))
        memory_min = float(np.min(mem_array))
        memory_max = float(np.max(mem_array))
        memory_current = float(mem_array[-1])
        
        if len(timestamps) >= 2:
            time_span = (timestamps[-1] - timestamps[0]) / 1000
            if time_span > 0:
                memory_growth_rate = (memory_current - memory_values[0]) / time_span
            else:
                memory_growth_rate = 0
        else:
            memory_growth_rate = 0
        
        memory_trend = self._determine_memory_trend(memory_values, memory_growth_rate)
        leak_risk = self._assess_leak_risk(memory_values, memory_growth_rate)
        
        memory_spike_count = self._count_memory_spikes(memory_values)
        
        return {
            'memory_avg': round(memory_avg, 2),
            'memory_min': round(memory_min, 2),
            'memory_max': round(memory_max, 2),
            'memory_current': round(memory_current, 2),
            'memory_growth_rate': round(memory_growth_rate, 2),
            'memory_trend': memory_trend,
            'leak_risk': leak_risk,
            'memory_spike_count': memory_spike_count
        }
    
    def analyze_cpu_usage(self) -> Dict[str, Any]:
        if len(self.cpu_history) < 5:
            return {
                'cpu_avg': 0,
                'cpu_min': 0,
                'cpu_max': 0,
                'cpu_current': 0,
                'cpu_trend': 'stable'
            }
        
        cpu_values = [cpu for _, cpu in self.cpu_history]
        cpu_array = np.array(cpu_values)
        
        cpu_avg = float(np.mean(cpu_array))
        cpu_min = float(np.min(cpu_array))
        cpu_max = float(np.max(cpu_array))
        cpu_current = float(cpu_array[-1])
        
        cpu_trend = self._determine_cpu_trend(cpu_values)
        
        return {
            'cpu_avg': round(cpu_avg, 2),
            'cpu_min': round(cpu_min, 2),
            'cpu_max': round(cpu_max, 2),
            'cpu_current': round(cpu_current, 2),
            'cpu_trend': cpu_trend
        }
    
    def analyze_gpu_usage(self) -> Dict[str, Any]:
        if len(self.gpu_history) < 5:
            return {
                'gpu_avg': 0,
                'gpu_min': 0,
                'gpu_max': 0,
                'gpu_current': 0,
                'gpu_trend': 'stable'
            }
        
        gpu_values = [gpu for _, gpu in self.gpu_history]
        gpu_array = np.array(gpu_values)
        
        gpu_avg = float(np.mean(gpu_array))
        gpu_min = float(np.min(gpu_array))
        gpu_max = float(np.max(gpu_array))
        gpu_current = float(gpu_array[-1])
        
        gpu_trend = self._determine_gpu_trend(gpu_values)
        
        return {
            'gpu_avg': round(gpu_avg, 2),
            'gpu_min': round(gpu_min, 2),
            'gpu_max': round(gpu_max, 2),
            'gpu_current': round(gpu_current, 2),
            'gpu_trend': gpu_trend
        }
    
    def analyze_battery_temp(self) -> Dict[str, Any]:
        if len(self.battery_temp_history) < 5:
            return {
                'temp_avg': 0,
                'temp_min': 0,
                'temp_max': 0,
                'temp_current': 0,
                'temp_trend': 'stable',
                'thermal_throttle_risk': 'low'
            }
        
        temp_values = [temp for _, temp in self.battery_temp_history]
        temp_array = np.array(temp_values)
        
        temp_avg = float(np.mean(temp_array))
        temp_min = float(np.min(temp_array))
        temp_max = float(np.max(temp_array))
        temp_current = float(temp_array[-1])
        
        temp_trend = self._determine_temp_trend(temp_values)
        thermal_throttle_risk = self._assess_thermal_risk(temp_current, temp_avg)
        
        return {
            'temp_avg': round(temp_avg, 1),
            'temp_min': round(temp_min, 1),
            'temp_max': round(temp_max, 1),
            'temp_current': round(temp_current, 1),
            'temp_trend': temp_trend,
            'thermal_throttle_risk': thermal_throttle_risk
        }
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        fps_analysis = self.analyze_fps_stability()
        memory_analysis = self.analyze_memory_trend()
        cpu_analysis = self.analyze_cpu_usage()
        gpu_analysis = self.analyze_gpu_usage()
        temp_analysis = self.analyze_battery_temp()
        
        overall_score = self._calculate_overall_score(
            fps_analysis, memory_analysis, cpu_analysis, gpu_analysis, temp_analysis
        )
        
        return {
            'fps': fps_analysis,
            'memory': memory_analysis,
            'cpu': cpu_analysis,
            'gpu': gpu_analysis,
            'battery_temp': temp_analysis,
            'overall_score': overall_score,
            'recommendations': self._generate_recommendations(
                fps_analysis, memory_analysis, cpu_analysis, gpu_analysis, temp_analysis
            )
        }
    
    def _calculate_stability_score(self, fps_avg: float, fps_std: float, 
                                   jank_rate: float, stutter_rate: float, 
                                   big_jank_count: int) -> float:
        score = 100.0
        
        fps_score = min(100, (fps_avg / 60.0) * 100)
        score = score * 0.4 + fps_score * 0.4
        
        std_penalty = min(30, fps_std * 2)
        score -= std_penalty
        
        jank_penalty = min(25, jank_rate * 2)
        score -= jank_penalty
        
        stutter_penalty = min(20, stutter_rate * 1.5)
        score -= stutter_penalty
        
        big_jank_penalty = min(15, big_jank_count * 3)
        score -= big_jank_penalty
        
        return max(0, score)
    
    def _get_stability_level(self, score: float) -> str:
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'
    
    def _determine_memory_trend(self, memory_values: List[float], 
                                growth_rate: float) -> str:
        if len(memory_values) < 3:
            return 'stable'
        
        recent_avg = np.mean(memory_values[-5:])
        early_avg = np.mean(memory_values[:5])
        
        if growth_rate > 1.0:
            return 'increasing_fast'
        elif growth_rate > 0.2:
            return 'increasing'
        elif growth_rate < -1.0:
            return 'decreasing_fast'
        elif growth_rate < -0.2:
            return 'decreasing'
        else:
            return 'stable'
    
    def _assess_leak_risk(self, memory_values: List[float], 
                         growth_rate: float) -> str:
        if len(memory_values) < 10:
            return 'low'
        
        if growth_rate > 2.0:
            return 'high'
        elif growth_rate > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _count_memory_spikes(self, memory_values: List[float]) -> int:
        if len(memory_values) < 5:
            return 0
        
        threshold = np.mean(memory_values) + 2 * np.std(memory_values)
        spike_count = np.sum(np.array(memory_values) > threshold)
        
        return int(spike_count)
    
    def _determine_cpu_trend(self, cpu_values: List[float]) -> str:
        if len(cpu_values) < 3:
            return 'stable'
        
        recent_avg = np.mean(cpu_values[-5:])
        early_avg = np.mean(cpu_values[:5])
        
        if recent_avg > early_avg * 1.3:
            return 'increasing'
        elif recent_avg < early_avg * 0.7:
            return 'decreasing'
        else:
            return 'stable'
    
    def _determine_gpu_trend(self, gpu_values: List[float]) -> str:
        if len(gpu_values) < 3:
            return 'stable'
        
        recent_avg = np.mean(gpu_values[-5:])
        early_avg = np.mean(gpu_values[:5])
        
        if recent_avg > early_avg * 1.3:
            return 'increasing'
        elif recent_avg < early_avg * 0.7:
            return 'decreasing'
        else:
            return 'stable'
    
    def _determine_temp_trend(self, temp_values: List[float]) -> str:
        if len(temp_values) < 3:
            return 'stable'
        
        recent_avg = np.mean(temp_values[-5:])
        early_avg = np.mean(temp_values[:5])
        
        if recent_avg > early_avg + 3:
            return 'increasing'
        elif recent_avg < early_avg - 3:
            return 'decreasing'
        else:
            return 'stable'
    
    def _assess_thermal_risk(self, temp_current: float, temp_avg: float) -> str:
        if temp_current > 45:
            return 'high'
        elif temp_current > 40:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_overall_score(self, fps_analysis: Dict, memory_analysis: Dict,
                                cpu_analysis: Dict, gpu_analysis: Dict,
                                temp_analysis: Dict) -> float:
        fps_score = fps_analysis.get('stability_score', 0)
        
        memory_score = 100
        if memory_analysis.get('leak_risk') == 'high':
            memory_score = 40
        elif memory_analysis.get('leak_risk') == 'medium':
            memory_score = 70
        
        cpu_score = 100
        if cpu_analysis.get('cpu_avg', 0) > 80:
            cpu_score = 50
        elif cpu_analysis.get('cpu_avg', 0) > 60:
            cpu_score = 75
        
        gpu_score = 100
        if gpu_analysis.get('gpu_avg', 0) > 80:
            gpu_score = 50
        elif gpu_analysis.get('gpu_avg', 0) > 60:
            gpu_score = 75
        
        temp_score = 100
        if temp_analysis.get('thermal_throttle_risk') == 'high':
            temp_score = 50
        elif temp_analysis.get('thermal_throttle_risk') == 'medium':
            temp_score = 75
        
        overall = (fps_score * 0.4 + memory_score * 0.25 + 
                  cpu_score * 0.15 + gpu_score * 0.1 + temp_score * 0.1)
        
        return round(overall, 1)
    
    def _generate_recommendations(self, fps_analysis: Dict, memory_analysis: Dict,
                                 cpu_analysis: Dict, gpu_analysis: Dict,
                                 temp_analysis: Dict) -> List[str]:
        recommendations = []
        
        if fps_analysis.get('stability_level') == 'poor':
            recommendations.append('FPS 稳定性较差，建议检查主线程耗时操作')
        
        if fps_analysis.get('jank_rate', 0) > 10:
            recommendations.append('卡顿率较高，建议优化渲染逻辑和减少过度绘制')
        
        if memory_analysis.get('leak_risk') == 'high':
            recommendations.append('检测到内存泄漏风险，建议使用 Memory Profiler 排查')
        
        if memory_analysis.get('memory_spike_count', 0) > 5:
            recommendations.append('内存波动较大，建议检查 Bitmap 缓存和对象分配')
        
        if cpu_analysis.get('cpu_avg', 0) > 70:
            recommendations.append('CPU 占用较高，建议优化后台任务和算法复杂度')
        
        if gpu_analysis.get('gpu_avg', 0) > 70:
            recommendations.append('GPU 负载较高，建议优化 Shader 和纹理资源')
        
        if temp_analysis.get('thermal_throttle_risk') == 'high':
            recommendations.append('设备温度过高，可能导致降频，建议优化功耗')
        
        if not recommendations:
            recommendations.append('整体性能表现良好，继续保持')
        
        return recommendations
    
    def reset(self):
        self.fps_history.clear()
        self.memory_history.clear()
        self.cpu_history.clear()
        self.jank_history.clear()
        self.gpu_history.clear()
        self.battery_temp_history.clear()
        self.data_count = 0
