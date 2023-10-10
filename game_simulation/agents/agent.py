import networkx as nx

from .text_generation_sm import generate, get_rating


class Agent:
    """
    A class to represent an individual agent in a simulation similar to The Sims.

    Attributes:
    -----------
    name : str
        The name of the agent.
    description : str
        A brief description of the agent.
    location : str
        The current location of the agent in the simulated environment.
    memories : list
        A list of memories the agent has about their interactions.
    compressed_memories : list
        A list of compressed memories that summarize the agent's experiences.
    plans : str
        The agent's daily plans, generated at the beginning of each day.

    Methods:
    --------
    plan(global_time, town_people, prompt_meta):
        Generates the agent's daily plan.
    
    execute_action(other_agents, location, global_time, town_areas, prompt_meta):
        Executes the agent's action based on their current situation and interactions with other agents.
    
    update_memories(other_agents, global_time, action_results):
        Updates the agent's memories based on their interactions with other agents.
    
    compress_memories(memory_ratings, global_time, MEMORY_LIMIT=10):
        Compresses the agent's memories to a more manageable and relevant set.
    
    rate_locations(locations, town_areas, global_time, prompt_meta):
        Rates different locations in the simulated environment based on the agent's preferences and experiences.
    """

    def __init__(self, name, description, starting_location, world_graph, use_openai):
        self.name = name
        self.description = description
        self.location = starting_location
        self.memory_ratings = []
        self.memories = []
        self.compressed_memories = []
        self.plans = ""
        self.world_graph = world_graph
        self.use_openai = use_openai

    def __repr__(self):
        return f"Agent({self.name}, {self.description}, {self.location})"

    def plan(self, global_time, prompt_meta):
        """
        Generates the agent's daily plan.
        
        Parameters:
        -----------
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to generate the plan.
        """
        prompt = "You are {}. " \
                 "The following is your description: {} You just woke up." \
                 "What is your goal for today? " \
                 "Write it down in an hourly basis, starting at {}:00. " \
                 "Write only one or two very short sentences. " \
                 "Be very brief. Use at most 50 words.".format(self.name, self.description, str(global_time))
        # print("plan prompt:\n", prompt)
        self.plans = generate(prompt_meta.format(prompt), self.use_openai)

    def execute_action(self, other_agents, location, global_time, town_areas, prompt_meta):

        """
        执行计划时综合考虑了：计划、所在地名字、所在地的描述、时间、所在地的所有人
        Executes the agent's action based on their current situation and interactions with other agents.
        
        Parameters:
        -----------
        other_agents : list
            A list of other Agent objects in the simulation.
        location : Location
            The current Location object where the agent is located.
        global_time : int
            The current time in the simulation.
        town_areas : dict
            A dictionary of Location objects representing different areas in the simulated environment.
        prompt_meta : str
            The prompt used to generate the action.

        Returns:
        --------
        action : str
            The action executed by the agent.
        """

        people = [agent.name for agent in other_agents if agent.location == location]

        prompt = "You are {}. " \
                 "Your plans are: {}. " \
                 "You are currently in {} with the following description: {}. " \
                 "It is currently {}:00. " \
                 "The following people are in this area: {}. " \
                 "You can interact with them.".format(self.name, self.plans, location.name, town_areas[location.name], str(global_time), ', '.join(people))

        people_description = [f"{agent.name}: {agent.description}" for agent in other_agents if agent.location == location.name]
        prompt += ' You know the following about people: ' + '. '.join(people_description)
        prompt += "What do you do in the next hour? Use at most 10 words to explain."

        # print("execute_action prompt:\n", prompt)
        action = generate(prompt_meta.format(prompt), self.use_openai)
        return action

    def update_memories(self, other_agents, global_time, action_results):

        """
        暂时未用到
        Updates the agent's memories based on their interactions with other agents.
        
        Parameters:
        -----------
        other_agents : list
            A list of other Agent objects in the simulation.
        global_time : int
            The current time in the simulation.
        action_results : dict
            A dictionary of the results of each agent's action.
        """

        for agent in other_agents:
            if agent.location == self.location:
                self.memories.append('[Time: {}. Person: {}. Memory: {}]\n'.format(str(global_time), agent.name, action_results[agent.name]))

    def compress_memories(self, global_time, memory_limit=10):

        """
        所谓压缩记忆，也就是根据记忆评分倒序取前N条记忆作为保留记忆
        Compresses the agent's memories to a more manageable and relevant set.
        
        Parameters:
        -----------
        global_time : int
            The current time in the simulation.
        MEMORY_LIMIT : int, optional
            The maximum number of memories to compress. Default is 10.

        Returns:
        --------
        memory_string : str
            The compressed memory string.
        """

        # self.memory_ratings列表中的每个元素都是一个元组（见memory_ratings.append((memory, rating, res))），元组的第一个元素通常是某个记忆，第二个元素是与该记忆相关的评分或权重。
        # 这段代码使用lambda x: x[1]将每个元组的第二个元素作为排序的关键因素。reverse=True参数表示按降序排序，也就是从高评分到低评分的顺序排序。
        # 将self.memory_ratings列表中的元素按照评分（权重）从高到低进行排序，最高评分的元素将排在列表的前面。这样，您可以很容易地找到具有最高评分的记忆或信息。
        memories_sorted = sorted(self.memory_ratings, key=lambda x: x[1], reverse=True)
        # 取前面N条的记忆
        relevant_memories = memories_sorted[:memory_limit]
        memory_string_to_compress = '.'.join([a[0] for a in relevant_memories])
        return '[Recollection at Time {}:00: {}]'.format(str(global_time), memory_string_to_compress)

    def rate_memories(self, locations, global_time, prompt_meta):

        """
        记忆打分时综合考虑了：计划、所在地、时间、记忆
        针对当前Agent在所在地所产生的记忆进行打分，将memories打分之后copy到memory_ratings里面
        Rates the agent's memories based on their relevance and importance.
        
        Parameters:
        -----------
        locations : Locations
            The Locations object representing different areas in the simulated environment.
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to rate the memories.

        Returns:
        --------
        memory_ratings : list
            A list of tuples representing the memory, its rating, and the generated response.
        """

        memory_ratings = []
        for memory in self.memories:
            prompt = "You are {}. " \
                     "Your plans are: {}. " \
                     "You are currently in {}. " \
                     "It is currently {}:00. " \
                     "You observe the following: {}. " \
                     "Give a rating, between 1 and 5, to how much you care about this.".format(self.name, self.plans, locations.get_location(self.location), str(global_time), memory)

            # print("rate_memories prompt:\n", prompt)
            # 通过LLM进行记忆的打分
            res = generate(prompt_meta.format(prompt), self.use_openai)

            # 获取LLM对记忆的打分
            rating = get_rating(res)
            max_attempts = 2
            current_attempt = 0
            while rating is None and current_attempt < max_attempts:
                rating = get_rating(res)
                current_attempt += 1
            if rating is None:
                rating = 0
            # 记录打分的记忆
            memory_ratings.append((memory, rating, res))
        self.memory_ratings = memory_ratings
        return memory_ratings

    def rate_locations(self, locations, global_time, prompt_meta):

        """
        地点打分时综合考虑了：计划、时间、所在地、所在地的描述
        根据代理的偏好和经验对模拟环境中的不同位置进行评分。然后根据打分排序，最后根据排序取第一位决定下一个位置去哪里
        Rates different locations in the simulated environment based on the agent's preferences and experiences.

        Parameters:
        -----------
        locations : Locations
            The Locations object representing different areas in the simulated environment.
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to rate the locations.

        Returns:
        --------
        place_ratings : list
            A list of tuples representing the location, its rating, and the generated response.

        """

        place_ratings = []
        for location in locations.locations.values():
            prompt = "You are {}. " \
                     "Your plans are: {}. " \
                     "It is currently {}:00. " \
                     "You are currently at {}. " \
                     "How likely are you to go to {} next?".format(self.name, self.plans, str(global_time), locations.get_location(self.location), location.name)
            res = generate(prompt_meta.format(prompt), self.use_openai)
            rating = get_rating(res)
            max_attempts = 2
            current_attempt = 0
            while rating is None and current_attempt < max_attempts:
                rating = get_rating(res)
                current_attempt += 1
            if rating is None:
                rating = 0
            place_ratings.append((location.name, rating, res))
        self.place_ratings = place_ratings
        return sorted(place_ratings, key=lambda x: x[1], reverse=True)

    def move(self, new_location_name):
        if new_location_name == self.location:
            return self.location

        try:
            # 使用了Python的NetworkX库来执行图论中的最短路径查找操作
            path = nx.shortest_path(self.world_graph, source=self.location, target=new_location_name)
            self.location = new_location_name
        except nx.NetworkXNoPath:
            print(f"No path found between {self.location} and {new_location_name}")
            return self.location

        return self.location
