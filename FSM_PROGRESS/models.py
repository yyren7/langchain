from django.db import models
from django.contrib.postgres.fields import JSONField

class PredefinedModule(models.Model):
    module_type = models.CharField(max_length=50, unique=True)  # 例如: "HTTP_REQUEST", "DATA_PROCESS"
    api_mappings = JSONField()  # {"method": "GET", "url": "/api/data", "headers": {...}}
    code_template = models.TextField()  # Jinja2模板
    input_schema = JSONField()  # JSON Schema
    output_schema = JSONField()

class StateMachine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fsm_definition = JSONField()  # 状态机结构
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)