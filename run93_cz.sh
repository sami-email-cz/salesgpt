#/bin/sh
set -x
export SERPAPI_API_KEY=c01381d590425cd30a769a0c1ee63c4eb8368ccbd8af1ff8cae6c664a4290d69

export OPENAI_API_KEY=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
export LANGCHAIN_TRACING=true

python3 run_cz.py --config agent_ester_tools_setup_cz.json --verbose True --max_num_turns 20
