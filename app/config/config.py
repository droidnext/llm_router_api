import os
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel

class Model(BaseModel):
    name: str

class Provider(BaseModel):
    api_base: str
    api_version: Optional[str] = None
    models: List[Model]

class Config:
    def __init__(self):
        self.config_path = os.getenv("CONFIG_PATH", "app/config/config.yaml")
        self.providers: Dict[str, Provider] = {}
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                for provider_name, provider_data in config_data.get('providers', {}).items():
                    self.providers[provider_name] = Provider(**provider_data)
        except Exception as e:
            raise Exception(f"Failed to load configuration: {str(e)}")

    def get_provider(self, provider_name: str) -> Provider:
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} is not supported")
        return self.providers[provider_name]

    def get_model(self, provider_name: str, model_name: str) -> Model:
        provider = self.get_provider(provider_name)
        for model in provider.models:
            if model.name == model_name:
                return model
        raise ValueError(f"Model {model_name} is not supported by provider {provider_name}")

    def get_supported_models(self) -> Dict[str, List[str]]:
        return {
            provider_name: [model.name for model in provider.models]
            for provider_name, provider in self.providers.items()
        } 