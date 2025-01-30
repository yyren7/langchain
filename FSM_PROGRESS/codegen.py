from jinja2 import Template

class CodeGenerator:
    def generate(self, fsm_def: dict) -> str:
        code_blocks = []
        for state in fsm_def['states']:
            module = PredefinedModule.objects.get(module_type=state['module_type'])
            template = Template(module.code_template)
            code_blocks.append(template.render(**state['parameters']))
        
        return self._wrap_executable(code_blocks)

    def _wrap_executable(self, blocks: list) -> str:
        return f"""
        def execute_pipeline():
            context = {{}}
            {'\n'.join(blocks)}
            return context
        """