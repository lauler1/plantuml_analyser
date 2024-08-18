import plantuml.plantuml_types as pt
import re
import asyncio

def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name.lower())

class PlantumlSimulation():
    """
    This class defines a PlantUML Simulation, which can generate sequence diagrams
    """
    def __init__(self, architecture, name=""):
        self.name = name
        self.architecture = architecture
        self.participants = {}
        self.part_seq = []
        self.sequence = []
        self.queues = {}
        
    def gather_participants(self, activities):
        owners = set()
        participants = {}
        for activity in activities:
            res = self.architecture.get_activity_owner(activity)
            owners.add(res)
        for owner in owners:
            if owner != None:
                color = "#96B1DA"
                
                if isinstance(owner, pt.PlantumlActor):
                    color = "#C6E6FF"
                sanitized_name = sanitize_name(owner.name)
                participants[sanitized_name] = f'participant "{owner.name}" as {sanitized_name} {color}'
        self.participants = participants

    def set_simulation_decorator(self, deco_text):
        self.sequence.append(deco_text)

    def set_simulation_activate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = self.architecture.get_activity_owner(component)
        self.sequence.append(f"activate {sanitize_name(component.name)}")

    def set_simulation_deactivate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = self.architecture.get_activity_owner(component)
        self.sequence.append(f"deactivate {sanitize_name(component.name)}")

    def set_simulation_activity_decorator(self, component):
        if not isinstance(component, pt.PlantumlActivity):
            return
        owner = self.architecture.get_activity_owner(component)
        self.sequence.append(f"rnote over {sanitize_name(owner.name)} #C5FFA6\n{component.name}\nendrnote")

    async def run(self, activities):
        # Run the list of coroutines concurrently
        await asyncio.gather(*(coro.run(self) for coro in activities))

    def simulate(self):
        activities = self.architecture.get_all_activities()
        self.part_seq = []
        self.sequence = []
        self.queues = {}
        
        print("@startuml")
        skinparam = """hide footbox
skinparam roundcorner 0
skinparam sequence {
LifeLineBackgroundColor #C5FFA6
LifeLineBorderColor #095C2E
ParticipantFontColor #4A4A97
ParticipantBorderColor #4A4A97
ParticipantBackgroundColor #96B1DA
}"""
        print(skinparam)

        self.gather_participants(activities)
        asyncio.run(self.run(list(activities)))
        
        new_list_of_participants = []
        for item in self.part_seq:
            if not item in new_list_of_participants:
                new_list_of_participants.append(item)
        
        for item in new_list_of_participants:
            print(self.participants[item])
        
        for item in self.sequence :
            print(item)
        
        print("@enduml")            

    def get_queue(self, connection):
    
        if isinstance(connection, pt.ObjectRef):
            connection = connection.ref
            
        if not connection.name in self.queues:
            self.queues[connection.name] = asyncio.Queue()
        return self.queues[connection.name]

    def print_transmission(self, connection, sender, text):
        send_name = sender.name 
        if isinstance(sender, pt.PlantumlActivity):
            send_name = self.architecture.get_activity_owner(sender).name
            
        if isinstance(connection, pt.ObjectRef):
            connection = connection.ref

        other = connection.comp1.ref
        if other == sender:
            other = connection.comp2.ref
        other_name = other.name 
        if isinstance(sender, pt.PlantumlActivity):
            other_name = self.architecture.get_activity_owner(other).name
        sanitized_send_name = sanitize_name(send_name)
        sanitized_other_name = sanitize_name(other_name)
        self.part_seq.append(sanitized_send_name)
        self.part_seq.append(sanitized_other_name)
        self.sequence.append(f"{sanitized_send_name} -> {sanitized_other_name}: {text}")
        
    async def send_message(self, connection, sender, lable, data=""):
        """
        Sends a message in the queue.
        This method also yields the control to the event loop after sending.
        """
        self.print_transmission(connection, sender, lable)
        await self.get_queue(connection).put({"label":lable, "data":data})

    async def send_message_and_wait(self, connection, sender, lable, data=""):
        """
        Sends a message and waits for an answer in the queue.
        """
        self.print_transmission(connection, sender, lable)
        self.get_queue(connection).put_nowait({"label":lable, "data":data})
        item = await self.get_queue().get()
        return item

    async def wait_message(self, connection):
        """
        Waits for a message in the queue.
        """
        item = await self.get_queue(connection).get()
        return item
