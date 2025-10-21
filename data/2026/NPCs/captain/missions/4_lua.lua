if state.calls == nil then
	state.calls = 0
end

state.calls = state.calls + 1

python.coroutine(say("Great, you've called " .. state.calls .. " times now!"))
