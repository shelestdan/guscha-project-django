from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class BehavioralAnalysis(models.Model):
    """
    Модель для хранения данных поведенческого анализа пользователей
    """
    
    RISK_LEVELS = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    ANALYSIS_TYPES = [
        ('mouse_movement', 'Движение мыши'),
        ('keystroke_dynamics', 'Динамика нажатий клавиш'),
        ('scroll_behavior', 'Поведение прокрутки'),
        ('click_patterns', 'Паттерны кликов'),
        ('form_filling', 'Заполнение форм'),
        ('navigation', 'Навигация'),
    ]
    
    # Основная информация
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='ID сессии'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    ip_address = models.GenericIPAddressField(
        db_index=True,
        verbose_name='IP адрес'
    )
    
    analysis_type = models.CharField(
        max_length=50,
        choices=ANALYSIS_TYPES,
        verbose_name='Тип анализа'
    )
    
    # Данные движения мыши
    mouse_movements = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Движения мыши'
    )
    
    mouse_velocity_avg = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Средняя скорость мыши'
    )
    
    mouse_acceleration_avg = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Среднее ускорение мыши'
    )
    
    # Данные нажатий клавиш
    keystroke_intervals = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Интервалы нажатий клавиш'
    )
    
    keystroke_dwell_times = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Время удержания клавиш'
    )
    
    typing_speed = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Скорость печати (символов в минуту)'
    )
    
    # Данные прокрутки
    scroll_events = models.JSONField(
        default=list,
        blank=True,
        verbose_name='События прокрутки'
    )
    
    scroll_velocity_avg = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Средняя скорость прокрутки'
    )
    
    # Данные кликов
    click_events = models.JSONField(
        default=list,
        blank=True,
        verbose_name='События кликов'
    )
    
    click_intervals = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Интервалы между кликами'
    )
    
    # Анализ риска
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='low',
        verbose_name='Уровень риска'
    )
    
    risk_score = models.IntegerField(
        default=0,
        verbose_name='Оценка риска (0-100)'
    )
    
    is_bot_like = models.BooleanField(
        default=False,
        verbose_name='Похоже на бота'
    )
    
    is_suspicious = models.BooleanField(
        default=False,
        verbose_name='Подозрительное поведение'
    )
    
    # Временные метки
    analysis_start = models.DateTimeField(
        verbose_name='Начало анализа'
    )
    
    analysis_end = models.DateTimeField(
        verbose_name='Конец анализа'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    
    # Дополнительные данные
    additional_metrics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные метрики'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Заметки'
    )
    
    class Meta:
        db_table = 'security_behavioral_analysis'
        verbose_name = 'Поведенческий анализ'
        verbose_name_plural = 'Поведенческие анализы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['analysis_type']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['is_bot_like']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Анализ {self.analysis_type} для сессии {self.session_id[:8]}..."
    
    def calculate_risk_score(self):
        """
        Вычисляет оценку риска на основе поведенческих данных
        """
        score = 0
        
        # Анализ движений мыши
        if self.mouse_velocity_avg is not None:
            # Слишком быстрые или слишком медленные движения подозрительны
            if self.mouse_velocity_avg > 1000 or self.mouse_velocity_avg < 10:
                score += 25
            
            # Слишком равномерные движения (как у бота)
            if self.mouse_acceleration_avg is not None and self.mouse_acceleration_avg < 5:
                score += 20
        
        # Анализ нажатий клавиш
        if self.typing_speed is not None:
            # Нечеловечески быстрая печать
            if self.typing_speed > 200:
                score += 30
            # Слишком равномерные интервалы
            if len(self.keystroke_intervals) > 5:
                intervals = self.keystroke_intervals
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                if variance < 10:  # Слишком мало вариации
                    score += 25
        
        # Анализ кликов
        if len(self.click_intervals) > 3:
            # Слишком равномерные интервалы между кликами
            intervals = self.click_intervals
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            if variance < 50:  # Слишком мало вариации
                score += 20
        
        # Анализ времени сессии
        if self.analysis_start and self.analysis_end:
            session_duration = (self.analysis_end - self.analysis_start).total_seconds()
            # Слишком короткие сессии с большой активностью
            total_events = len(self.mouse_movements) + len(self.click_events) + len(self.scroll_events)
            if session_duration < 60 and total_events > 50:
                score += 35
        
        self.risk_score = min(score, 100)
        
        # Обновляем флаги
        self.is_bot_like = self.risk_score >= 70
        self.is_suspicious = self.risk_score >= 50
        
        # Обновляем уровень риска
        if self.risk_score >= 80:
            self.risk_level = 'critical'
        elif self.risk_score >= 60:
            self.risk_level = 'high'
        elif self.risk_score >= 40:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'
        
        return self.risk_score
    
    def add_mouse_movement(self, x, y, timestamp):
        """
        Добавляет данные о движении мыши
        """
        movement = {
            'x': x,
            'y': y,
            'timestamp': timestamp
        }
        self.mouse_movements.append(movement)
        
        # Вычисляем скорость и ускорение
        if len(self.mouse_movements) >= 2:
            self._calculate_mouse_metrics()
    
    def add_keystroke(self, key, press_time, release_time):
        """
        Добавляет данные о нажатии клавиши
        """
        dwell_time = release_time - press_time
        self.keystroke_dwell_times.append(dwell_time)
        
        # Вычисляем интервалы между нажатиями
        if len(self.keystroke_dwell_times) >= 2:
            last_keystroke = self.keystroke_dwell_times[-2]
            interval = press_time - (last_keystroke + self.keystroke_dwell_times[-2])
            self.keystroke_intervals.append(interval)
    
    def add_click(self, x, y, timestamp, button='left'):
        """
        Добавляет данные о клике
        """
        click = {
            'x': x,
            'y': y,
            'timestamp': timestamp,
            'button': button
        }
        self.click_events.append(click)
        
        # Вычисляем интервалы между кликами
        if len(self.click_events) >= 2:
            prev_click = self.click_events[-2]
            interval = timestamp - prev_click['timestamp']
            self.click_intervals.append(interval)
    
    def _calculate_mouse_metrics(self):
        """
        Вычисляет метрики движения мыши
        """
        if len(self.mouse_movements) < 2:
            return
        
        velocities = []
        accelerations = []
        
        for i in range(1, len(self.mouse_movements)):
            prev = self.mouse_movements[i-1]
            curr = self.mouse_movements[i]
            
            # Вычисляем расстояние и время
            dx = curr['x'] - prev['x']
            dy = curr['y'] - prev['y']
            distance = (dx**2 + dy**2)**0.5
            time_diff = curr['timestamp'] - prev['timestamp']
            
            if time_diff > 0:
                velocity = distance / time_diff
                velocities.append(velocity)
                
                # Вычисляем ускорение
                if len(velocities) >= 2:
                    acceleration = (velocities[-1] - velocities[-2]) / time_diff
                    accelerations.append(acceleration)
        
        if velocities:
            self.mouse_velocity_avg = sum(velocities) / len(velocities)
        
        if accelerations:
            self.mouse_acceleration_avg = sum(accelerations) / len(accelerations)