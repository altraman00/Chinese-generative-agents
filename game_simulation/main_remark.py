import json

import networkx as nx

from agents.agent import Agent
from agents.text_generation_sm import summarize_simulation
from locations.locations import Locations

# Set default value for prompt_meta if not defined elsewhere
prompt_meta = '### Instruction:\n{}\n### Response:'

# Initialize global time and simulation variables
global_time = 0
repeats = 1

# log_locations = False
log_locations = False
log_actions = True
log_plans = True
log_ratings = True
log_memories = True

print_locations = True
print_actions = True
print_plans = True
print_ratings = True
print_memories = True

use_openai = True

# Start simulation loop
whole_simulation_output = ""

# Load town areas and people from JSON file
with open('simulation_config.json', 'r') as f:
    town_data = json.load(f)

town_people = town_data['town_people']
town_areas = town_data['town_areas']

# Create world_graph
world_graph = nx.Graph()
last_town_area = None
for town_area in town_areas.keys():
    world_graph.add_node(town_area)
    world_graph.add_edge(town_area, town_area)  # Add an edge to itself
    if last_town_area is not None:
        world_graph.add_edge(town_area, last_town_area)
    last_town_area = town_area

# Add the edge between the first and the last town areas to complete the cycle
world_graph.add_edge(list(town_areas.keys())[0], last_town_area)

# # 绘制出城镇图
# pos = nx.spring_layout(world_graph)  # 指定布局
# nx.draw(world_graph, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=10)
# plt.show()


# Initialize agents and locations
agents = []
locations = Locations()

for name, description in town_people.items():
    starting_location = description['starting_location']
    people_desc = description['description']
    agents.append(Agent(name, people_desc, starting_location, world_graph, use_openai))

for name, description in town_areas.items():
    locations.add_location(name, description)

print(agents)
print(locations)

for repeat in range(repeats):
    # log_output for one repeat
    log_output = ""

    print(f"====================== REPEAT {repeat} ======================\n")
    log_output += f"====================== REPEAT {repeat} ======================\n"
    if log_locations:
        log_output += f"=== LOCATIONS AT START OF REPEAT {repeat} ===\n"
        log_output += str(locations) + "\n"
        if print_locations:
            print(f"=== LOCATIONS AT START OF REPEAT {repeat} ===")
            print(str(locations) + "\n")

    # Plan actions for each agent
    for agent in agents:
        print(f"================================={agent.name}'s Plan===============================")
        agent.plan(global_time, prompt_meta)
        if log_plans:
            log_output += f"{agent.name} plans: {agent.plans}\n"
            # print(f"\nPlan:log_output:{log_output}")
            if print_plans:
                print("\nPlan:--------------\n")
                print(f"{agent.name} plans: {agent.plans}")

    print(f"****************************************************Execute Action****************************************************")

    # 执行计划的行动并更新记忆
    # Execute planned actions and update memories
    for agent in agents:
        print(f"================================={agent.name} Execute Action===============================")
        # Execute action
        action = agent.execute_action(agents, locations.get_location(agent.location), global_time, town_areas, prompt_meta)
        if log_actions:
            log_output += f"{agent.name} action: {action}\n"
            # print(f"\nExecute Action:log_output:{log_output}\n")
            if print_actions:
                print("\nAction:--------------\n")
                print(f"{agent.name} action: {action}")

        # Update memories：将当前Agent的Action更新到其他所有Agent的记忆中，让其他Agent知道你做了什么
        for other_agent in agents:
            print(f"================================={other_agent.name} Update Memories about to {agent.name}===============================")
            if other_agent != agent:
                memory = f'[Time: {global_time}. Person: {agent.name}. Memory: {action}]'
                other_agent.memories.append(memory)
                if log_memories:
                    log_output += f"{other_agent.name} remembers: {memory}\n"
                    # print(f"\nUpdate Memories:log_output:{log_output}\n")
                    if print_memories:
                        print(f"{other_agent.name} remembers: {memory}")

        # 对每个代理的记忆进行压缩和评级打分
        # Compress and rate memories for each agent
        for agent in agents:
            # 提炼重要记忆来进行压缩
            agent.compress_memories(global_time)
            # 对记忆打分，便于上一步的记忆提炼（压缩）
            agent.rate_memories(locations, global_time, prompt_meta)
            if log_ratings:
                log_output += f"{agent.name} memory ratings: {agent.memory_ratings}\n"
                # print(f"\nCompress Memories:log_output:{log_output}\n")
                if print_ratings:
                    print(f"{agent.name} memory ratings: {agent.memory_ratings}")

    print(f"***************************************************Rate Locations****************************************************")

    # 对地点进行打分，用于后续决定下一步去哪个地方
    # Rate locations and determine where agents will go next
    for agent in agents:
        place_ratings = agent.rate_locations(locations, global_time, prompt_meta)
        if log_ratings:
            log_output += f"=== UPDATED LOCATION RATINGS {global_time} FOR {agent.name}===\n"
            log_output += f"{agent.name} location ratings: {place_ratings}\n"
            # print(f"\nRate Locations:log_output:{log_output}\n")
            if print_ratings:
                print(f"=== UPDATED LOCATION RATINGS {global_time} FOR {agent.name}===\n")
                print(f"{agent.name} location ratings: {place_ratings}\n")

        old_location = agent.location
        # 根据对地点打分并倒序排列后取第一位作为下一个地点
        new_location_name = place_ratings[0][0]
        agent.move(new_location_name)

        if print_locations:
            log_output += f"=== UPDATED LOCATIONS AT TIME {global_time} FOR {agent.name}===\n"
            log_output += f"{agent.name} moved from {old_location} to {new_location_name}\n"
            # print(f"\nlog_output:{log_output}\n")
        if print_ratings:
            print(f"=== UPDATED LOCATIONS AT TIME {global_time} FOR {agent.name}===\n")
            print(f"{agent.name} moved from {old_location} to {new_location_name}\n")
            # print(f"\nlog_output:{log_output}\n")

    print(f"****************************************************SUMMARY FOR REPEAT {repeat}****************************************************")

    print(summarize_simulation(log_output=log_output))

    whole_simulation_output += log_output

    # Increment time
    global_time += 1

# Write log output to file
with open('simulation_log_1.txt', 'w') as f:
    f.write(whole_simulation_output)
