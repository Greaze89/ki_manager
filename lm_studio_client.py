"""
LM Studio API Client für KI-Analyse
"""

import requests
import json
import logging
import time
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass
from pathlib import Path

from utils.logger import log_function_call, log_performance

@dataclass
class LMStudioConfig:
    """Konfiguration für LM Studio"""
    base_url: str = "http://localhost:1234"
    model_name: str = "qwen2.5-7b-instruct"
    timeout: int = 120
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    stream: bool = False

class LMStudioError(Exception):
    """Custom Exception für LM Studio Fehler"""
    pass

class LMStudioClient:
    """Client für LM Studio API-Kommunikation"""
    
    def __init__(self, config: LMStudioConfig = None):
        self.config = config or LMStudioConfig()
        self.logger = logging.getLogger("ki_manager.lm_studio")
        self.session = requests.Session()
        
        # Request Headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        self.logger.info(f"LM Studio Client initialisiert: {self.config.base_url}")
    
    @log_function_call
    def check_connection(self) -> bool:
        """
        Prüft Verbindung zu LM Studio
        
        Returns:
            True wenn verbunden, False sonst
        """
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/models",
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                available_models = [model.get('id', '') for model in models.get('data', [])]
                
                self.logger.info(f"Verfügbare Modelle: {available_models}")
                
                # Prüfe ob unser Modell verfügbar ist
                model_available = any(self.config.model_name.lower() in model.lower() 
                                    for model in available_models)
                
                if not model_available:
                    self.logger.warning(f"Modell '{self.config.model_name}' nicht in verfügbaren Modellen gefunden")
                    # Nehme erstes verfügbares Modell als Fallback
                    if available_models:
                        self.config.model_name = available_models[0]
                        self.logger.info(f"Verwende Fallback-Modell: {self.config.model_name}")
                
                return True
            else:
                self.logger.error(f"Verbindung fehlgeschlagen: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Verbindung zu LM Studio fehlgeschlagen: {e}")
            return False
    
    @log_performance
    def generate_completion(self, 
                          messages: List[Dict[str, str]], 
                          **kwargs) -> Dict:
        """
        Generiert Text-Completion über LM Studio
        
        Args:
            messages: Chat-Messages im OpenAI Format
            **kwargs: Zusätzliche Parameter (temperature, max_tokens, etc.)
            
        Returns:
            API Response Dictionary
            
        Raises:
            LMStudioError: Bei API-Fehlern
        """
        
        # Parameter zusammenführen
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "stream": kwargs.get('stream', self.config.stream)
        }
        
        # Optional parameters nur hinzufügen wenn gesetzt
        for param in ['stop', 'presence_penalty', 'frequency_penalty']:
            if param in kwargs:
                params[param] = kwargs[param]
        
        self.logger.debug(f"Sende Request mit {len(messages)} Messages")
        
        # Retry-Logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    json=params,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Logging
                    usage = result.get('usage', {})
                    self.logger.info(
                        f"Completion erfolgreich: "
                        f"Prompt={usage.get('prompt_tokens', 0)} tokens, "
                        f"Completion={usage.get('completion_tokens', 0)} tokens"
                    )
                    
                    return result
                    
                elif response.status_code == 422:
                    # Validation Error - nicht retry-fähig
                    error_detail = response.json().get('detail', 'Validation Error')
                    raise LMStudioError(f"Validierungsfehler: {error_detail}")
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    self.logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                    last_error = LMStudioError(error_msg)
                    
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.info(f"Retry in {wait_time} seconds...")
                        time.sleep(wait_time)
                    
            except requests.exceptions.Timeout:
                error_msg = f"Timeout nach {self.config.timeout} Sekunden"
                self.logger.warning(f"Attempt {attempt + 1} timeout")
                last_error = LMStudioError(error_msg)
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Netzwerk-Fehler: {e}"
                self.logger.warning(f"Attempt {attempt + 1} network error: {e}")
                last_error = LMStudioError(error_msg)
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        # Alle Versuche fehlgeschlagen
        raise last_error or LMStudioError("Unbekannter Fehler")
    
    def generate_streaming_completion(self, 
                                    messages: List[Dict[str, str]], 
                                    **kwargs) -> Generator[str, None, None]:
        """
        Generiert Streaming-Completion
        
        Args:
            messages: Chat-Messages
            **kwargs: Zusätzliche Parameter
            
        Yields:
            Chunks des generierten Texts
        """
        
        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "stream": True
        }
        
        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/chat/completions",
                json=params,
                timeout=self.config.timeout,
                stream=True
            )
            
            if response.status_code != 200:
                raise LMStudioError(f"Streaming failed: HTTP {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    
                    if line_text.startswith('data: '):
                        data_text = line_text[6:]  # Remove 'data: '
                        
                        if data_text.strip() == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_text)
                            choices = data.get('choices', [])
                            
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                
                                if content:
                                    yield content
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            raise LMStudioError(f"Streaming error: {e}")
    
    def extract_response_text(self, response: Dict) -> str:
        """
        Extrahiert Text aus API-Response
        
        Args:
            response: LM Studio API Response
            
        Returns:
            Generierter Text
        """
        try:
            choices = response.get('choices', [])
            if not choices:
                raise LMStudioError("Keine Antwort-Choices in Response")
            
            message = choices[0].get('message', {})
            content = message.get('content', '')
            
            if not content:
                raise LMStudioError("Leere Antwort erhalten")
            
            return content.strip()
            
        except (KeyError, IndexError) as e:
            raise LMStudioError(f"Fehler beim Extrahieren der Antwort: {e}")
    
    def get_model_info(self) -> Dict:
        """
        Holt Informationen über das aktuelle Modell
        
        Returns:
            Model-Informationen
        """
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/models",
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                
                for model in models.get('data', []):
                    if model.get('id', '').lower() == self.config.model_name.lower():
                        return model
                
                # Fallback: erstes Modell
                if models.get('data'):
                    return models['data'][0]
            
            return {}
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Fehler beim Abrufen der Model-Info: {e}")
            return {}
    
    def estimate_tokens(self, text: str) -> int:
        """
        Schätzt Token-Anzahl für Text (grobe Approximation)
        
        Args:
            text: Input-Text
            
        Returns:
            Geschätzte Token-Anzahl
        """
        # Grobe Schätzung: ~4 Zeichen pro Token für deutsche/englische Texte
        return len(text) // 4
    
    def validate_request_size(self, messages: List[Dict[str, str]]) -> bool:
        """
        Validiert ob Request-Größe im Limit liegt
        
        Args:
            messages: Chat-Messages
            
        Returns:
            True wenn OK, False wenn zu groß
        """
        total_text = ""
        for message in messages:
            total_text += message.get('content', '')
        
        estimated_tokens = self.estimate_tokens(total_text)
        
        # Conservativ: 70% der max_tokens für Input
        max_input_tokens = int(self.config.max_tokens * 0.7)
        
        if estimated_tokens > max_input_tokens:
            self.logger.warning(
                f"Request möglicherweise zu groß: {estimated_tokens} > {max_input_tokens} tokens"
            )
            return False
        
        return True
    
    def close(self):
        """Schließt HTTP-Session"""
        self.session.close()
        self.logger.debug("LM Studio Client Session geschlossen")

def test_lm_studio_connection():
    """Test-Funktion für LM Studio Verbindung"""
    client = LMStudioClient()
    
    print("🔍 Teste LM Studio Verbindung...")
    
    if not client.check_connection():
        print("❌ Verbindung fehlgeschlagen!")
        print("💡 Stellen Sie sicher, dass:")
        print("   • LM Studio läuft (http://localhost:1234)")
        print("   • Ein Modell geladen ist")
        print("   • Der Local Server aktiviert ist")
        return False
    
    print("✅ Verbindung erfolgreich!")
    
    # Test-Completion
    try:
        print("\n🤖 Teste Text-Generierung...")
        
        messages = [
            {
                "role": "system",
                "content": "Du bist ein hilfreicher Assistent."
            },
            {
                "role": "user", 
                "content": "Schreibe einen kurzen Satz über Künstliche Intelligenz."
            }
        ]
        
        response = client.generate_completion(messages, max_tokens=100)
        text = client.extract_response_text(response)
        
        print(f"🎯 Antwort: {text}")
        print("✅ Text-Generierung erfolgreich!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        return False
    
    finally:
        client.close()

if __name__ == "__main__":
    test_lm_studio_connection()