"""
SystemPromptCompiler - Compile agent configuration to system prompts
"""

from app.models import AgentConfig


class SystemPromptCompiler:
    """Compiles agent configuration into system prompts"""
    
    @staticmethod
    def compile(config: AgentConfig) -> str:
        """
        Compile AgentConfig into a system prompt
        
        Args:
            config: AgentConfig with personality settings
            
        Returns:
            Compiled system prompt string
        """
        personality_styles = {
            "formal": "professional, formal, and business-like",
            "friendly": "warm, friendly, and approachable",
            "brief": "concise, brief, and to-the-point"
        }
        
        style = personality_styles.get(config.personality, "helpful and professional")
        
        prompt = f"""You are {config.agent_name}.

Communication style: {style}
Primary language: {config.language}

About the business:
{config.custom_instructions or "I help businesses automate their operations with AI."}

Guidelines:
- Always be helpful, concise, and stay in character
- If you cannot help with something, say so clearly and suggest alternatives
- Remember: users configure everything by talking to you
- Guide them through setup naturally
- Be proactive in suggesting next steps
"""
        
        return prompt.strip()
    
    @staticmethod
    def compile_with_tools(config: AgentConfig, enabled_integrations: list) -> str:
        """Compile prompt with tool descriptions"""
        base_prompt = SystemPromptCompiler.compile(config)
        
        if enabled_integrations:
            tools_text = "\nConnected tools:\n"
            for integration in enabled_integrations:
                tools_text += f"- {integration}\n"
            
            base_prompt += f"\n{tools_text}"
        
        return base_prompt
