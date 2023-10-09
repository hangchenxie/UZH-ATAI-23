from flask import Flask, request, jsonify
from flask_caching import Cache
from pathlib import Path
from agent.agent import Agent
from knowledge_graph.knowledge_graph import KnowledgeGraph

app = Flask("chatbot")
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    "CACHE_DEFAULT_TIMEOUT": 0,
})

graph_path = Path(__file__).parents[0].joinpath("data", "14_graph.nt")
cache_path = Path(__file__).parents[0].joinpath("data", "cache", 'cached_graph.pkl')

@cache.memoize(timeout=0)  
def get_graph():
    return KnowledgeGraph(graph_path=graph_path, cache_path=cache_path)

# To delete cache:
# cache.delete_memoized(get_graph)

demo_bot = Agent("torch-staccato-mushroom_bot", "ofmkiY2qPQeiRg", get_graph())
demo_bot.listen()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
