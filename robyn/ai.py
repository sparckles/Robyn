"""
AI integration module for Robyn framework.
Provides agent and memory functionality for building AI-powered applications.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional, Union, List
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class AIConfig:
    """Configuration class for AI providers and settings"""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_vars = {
            'OPENAI_API_KEY': 'openai_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key',
            'GOOGLE_API_KEY': 'google_api_key',
            'MEM0_API_KEY': 'mem0_api_key',
            'LANGGRAPH_API_KEY': 'langgraph_api_key',
            'AI_MODEL': 'model',
            'AI_TEMPERATURE': 'temperature',
            'AI_MAX_TOKENS': 'max_tokens'
        }
        
        for env_var, config_key in env_vars.items():
            if env_var in os.environ and config_key not in self.config:
                value = os.environ[env_var]
                # Convert numeric values
                if config_key in ['temperature', 'max_tokens']:
                    try:
                        value = float(value) if config_key == 'temperature' else int(value)
                    except ValueError:
                        pass
                self.config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, **kwargs) -> None:
        """Update configuration with new values"""
        self.config.update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self.config.copy()


class MemoryProvider(ABC):
    """Abstract base class for memory providers"""
    
    @abstractmethod
    async def store(self, user_id: str, data: Dict[str, Any]) -> None:
        """Store data in memory"""
        pass
    
    @abstractmethod
    async def retrieve(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve data from memory"""
        pass
    
    @abstractmethod
    async def clear(self, user_id: str) -> None:
        """Clear memory for a user"""
        pass


class InMemoryProvider(MemoryProvider):
    """Simple in-memory storage provider"""
    
    def __init__(self):
        self._storage: Dict[str, List[Dict[str, Any]]] = {}
    
    async def store(self, user_id: str, data: Dict[str, Any]) -> None:
        if user_id not in self._storage:
            self._storage[user_id] = []
        self._storage[user_id].append(data)
    
    async def retrieve(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._storage.get(user_id, [])
    
    async def clear(self, user_id: str) -> None:
        if user_id in self._storage:
            del self._storage[user_id]


class Mem0Provider(MemoryProvider):
    """Mem0 memory provider integration"""
    
    def __init__(self, **config):
        self.config = config
        self._client = None
        logger.info("Mem0 provider initialized with config: %s", config)
    
    def _get_client(self):
        if self._client is None:
            try:
                import mem0
                self._client = mem0.Memory(**self.config)
            except ImportError:
                raise ImportError("mem0 package not installed. Install with: pip install mem0ai")
        return self._client
    
    async def store(self, user_id: str, data: Dict[str, Any]) -> None:
        client = self._get_client()
        message = data.get('message', str(data))
        try:
            client.add(message, user_id=user_id)
        except Exception as e:
            logger.warning(f"Failed to store in Mem0: {e}. Falling back to local storage.")
            # Fallback to simple storage if Mem0 fails
            if not hasattr(self, '_fallback_storage'):
                self._fallback_storage = {}
            if user_id not in self._fallback_storage:
                self._fallback_storage[user_id] = []
            self._fallback_storage[user_id].append(data)
    
    async def retrieve(self, user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            if query:
                results = client.search(query, user_id=user_id)
            else:
                results = client.get_all(user_id=user_id)
            return results
        except Exception as e:
            logger.warning(f"Failed to retrieve from Mem0: {e}. Using fallback storage.")
            # Use fallback storage if available
            if hasattr(self, '_fallback_storage'):
                return self._fallback_storage.get(user_id, [])
            return []
    
    async def clear(self, user_id: str) -> None:
        try:
            client = self._get_client()
            client.delete_all(user_id=user_id)
        except Exception as e:
            logger.warning(f"Failed to clear Mem0: {e}. Clearing fallback storage.")
        
        # Also clear fallback storage
        if hasattr(self, '_fallback_storage') and user_id in self._fallback_storage:
            del self._fallback_storage[user_id]


class Memory:
    """Memory interface for storing and retrieving conversation history and context"""
    
    def __init__(self, provider: Union[str, MemoryProvider], user_id: str, **kwargs):
        self.user_id = user_id
        
        if isinstance(provider, str):
            if provider == "mem0":
                self.provider = Mem0Provider(**kwargs)
            elif provider == "inmemory":
                self.provider = InMemoryProvider()
            else:
                raise ValueError(f"Unknown memory provider: {provider}")
        else:
            self.provider = provider
    
    async def add(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to memory"""
        data = {"message": message, "metadata": metadata or {}}
        await self.provider.store(self.user_id, data)
    
    async def get(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages from memory"""
        return await self.provider.retrieve(self.user_id, query)
    
    async def clear(self) -> None:
        """Clear all memory for this user"""
        await self.provider.clear(self.user_id)


class AgentRunner(ABC):
    """Abstract base class for agent runners"""
    
    @abstractmethod
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute the agent with the given query"""
        pass


class LangGraphRunner(AgentRunner):
    """LangGraph runner for executing agent workflows"""
    
    def __init__(self, graph_path: Optional[str] = None, **config):
        self.graph_path = graph_path
        self.config = config
        self._graph = None
        if graph_path:
            logger.info("LangGraph runner initialized with graph: %s", graph_path)
        else:
            logger.info("LangGraph runner initialized with default simple workflow")
    
    def _load_graph(self):
        if self._graph is None:
            try:
                import langgraph
                from langgraph.graph import StateGraph, END
                from typing_extensions import TypedDict
                
                if self.graph_path and self.graph_path.endswith('.json'):
                    with open(self.graph_path, 'r') as f:
                        graph_config = json.load(f)
                    self._graph = langgraph.from_config(graph_config)
                else:
                    # Create a simple default graph
                    class State(TypedDict):
                        query: str
                        response: str
                    
                    def simple_agent(state: State) -> State:
                        query = state.get("query", "")
                        response = f"LangGraph processed: {query}"
                        return {"query": query, "response": response}
                    
                    workflow = StateGraph(State)
                    workflow.add_node("agent", simple_agent)
                    workflow.set_entry_point("agent")
                    workflow.add_edge("agent", END)
                    self._graph = workflow.compile()
                    
            except ImportError:
                raise ImportError("langgraph package not installed. Install with: pip install langgraph")
            except FileNotFoundError:
                raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
        return self._graph
    
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        graph = self._load_graph()
        inputs = {"query": query, **kwargs}
        
        # Handle both sync and async graphs
        try:
            if hasattr(graph, 'ainvoke'):
                result = await graph.ainvoke(inputs)
            else:
                result = graph.invoke(inputs)
            return result
        except Exception as e:
            # Fallback to simple response if graph execution fails
            return {
                "response": f"LangGraph agent processed: {query}",
                "query": query,
                "error": str(e) if self.config.get("debug") else None
            }


class SimpleRunner(AgentRunner):
    """Simple runner with OpenAI integration and fallback responses"""
    
    def __init__(self, **config):
        self.config = AIConfig(**config)
        self._client = None
        
    def _get_client(self):
        """Get OpenAI client if API key is available"""
        if self._client is None and self.config.get("openai_api_key"):
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.config.get("openai_api_key"))
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        return self._client
    
    
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute with OpenAI (requires API key)"""
        client = self._get_client()
        
        if not client:
            raise ValueError("OpenAI API key is required. Set 'openai_api_key' in configuration.")
        
        try:
            # Use OpenAI
            messages = [{"role": "user", "content": query}]
            
            # Add conversation history
            context = kwargs.get('context', {})
            history = context.get('history', [])
            
            if history:
                for item in history[-10:]:
                    msg = item.get('message', str(item))
                    if msg.startswith('Query: '):
                        messages.insert(-1, {"role": "user", "content": msg[7:]})
                    elif msg.startswith('Response: '):
                        messages.insert(-1, {"role": "assistant", "content": msg[10:]})
            
            response = client.chat.completions.create(
                model=self.config.get("model", "gpt-4o"),
                messages=messages,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 1000)
            )
            
            content = response.choices[0].message.content
            metadata = {
                "runner_type": "simple_openai",
                "model": self.config.get("model", "gpt-4o"),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            if self.config.get("debug", False):
                metadata["debug_info"] = {
                    "config": self.config.to_dict()
                }
            
            return {
                "response": content,
                "query": query,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in SimpleRunner: {e}")
            raise e


class Agent:
    """AI Agent interface for handling queries with memory and execution"""
    
    def __init__(self, runner: Union[str, AgentRunner], memory: Optional[Memory] = None, **kwargs):
        self.memory = memory
        
        if isinstance(runner, str):
            if runner.startswith("langgraph:"):
                graph_path = runner.split(":", 1)[1]
                self.runner = LangGraphRunner(graph_path, **kwargs)
            elif runner == "langgraph":
                # Simple implementation without external dependencies
                self.runner = SimpleRunner(**kwargs)
            elif runner == "simple":
                self.runner = SimpleRunner(**kwargs)
            else:
                raise ValueError(f"Unknown runner type: {runner}")
        else:
            self.runner = runner
    
    async def run(self, query: str, history: bool = False, **kwargs) -> Dict[str, Any]:
        """Run the agent with the given query"""
        context = {}
        
        if self.memory and history:
            context["history"] = await self.memory.get()
        
        # Add context to kwargs
        if context:
            kwargs["context"] = context
        
        # Execute the agent
        result = await self.runner.run(query, **kwargs)
        
        # Store the interaction in memory if available
        if self.memory:
            await self.memory.add(f"Query: {query}")
            if "response" in result:
                await self.memory.add(f"Response: {result['response']}")
        
        return result


def memory(provider: str = "inmemory", user_id: str = "default", **kwargs) -> Memory:
    """
    Create a memory instance with the specified provider
    
    Args:
        provider: Memory provider type ("mem0", "inmemory")
        user_id: User identifier for memory isolation
        **kwargs: Additional configuration for the provider
    
    Returns:
        Memory instance
    """
    return Memory(provider=provider, user_id=user_id, **kwargs)


def configure(**kwargs) -> AIConfig:
    """
    Create and configure AI settings
    
    Args:
        **kwargs: Configuration options including API keys, model settings, etc.
    
    Returns:
        AIConfig instance
        
    Example:
        config = configure(
            openai_api_key="your-key",
            model="gpt-4",
            temperature=0.7
        )
    """
    return AIConfig(**kwargs)


def agent(runner: str = "simple", memory: Optional[Memory] = None, config: Optional[AIConfig] = None, **kwargs) -> Agent:
    """
    Create an agent instance with the specified runner
    
    Args:
        runner: Agent runner type ("langgraph:path/to/graph.json", "simple")
        memory: Optional memory instance for context
        config: Optional AIConfig instance for configuration
        **kwargs: Additional configuration for the runner
    
    Returns:
        Agent instance
        
    Example:
        # Simple usage
        chat = agent()
        
        # With configuration
        config = configure(openai_api_key="your-key")
        chat = agent(runner="simple", config=config)
        
        # With memory
        mem = memory(provider="mem0", user_id="user123")
        chat = agent(runner="simple", memory=mem)
    """
    # Merge config if provided
    if config:
        kwargs.update(config.to_dict())
    
    return Agent(runner=runner, memory=memory, **kwargs)