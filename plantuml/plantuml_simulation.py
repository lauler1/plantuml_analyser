import plantuml.plantuml_types as pt
import re
import asyncio

def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name.lower())

class PlantumlSimulation():
    """
    This class defines a PlantUML Simulation, which can generate sequence diagrams
    """
    def __init__(self, architecture, name="", **options):
        """
        Simulates an architecture and generates a sequence diagram.
        
        architecture: An architecture to be simulated.
        name: Simulation name.
        options:
            comp_order: List of components paths inside the architecture. Used to prioritize participant showed in the sequence in the diagram.
        """
        self.name = name
        self.architecture = architecture
        self.participants = {}
        self.part_seq = [] # Store seq of participants during a simulation simulation.
        self.sequence = [] # Store sequence of activities during a simulation simulation
        self.queues = {}
        
        self.metadata_dict = {"comp_order":[]}
        self.metadata_dict.update(options)

    def set_options(self, **options):
        """
        Update the options, refer to the main constructor for more details.
        """
        # Update the metadata_dict with the provided options
        self.metadata_dict.update(options)
        
    def gather_participants(self, activities):
        owners = set()
        participants = {}
        
        # Create a set of owners, because sequences are shown per component, not per activity
        for activity in activities:
            # res = self.architecture.get_activity_owner(activity)
            owners.add(activity.owner.ref)
            
        # Create a dictionary of Owners (i.e. components owning the activities)
        for owner in owners:
            if owner != None:
                color = "#96B1DA"
                
                if isinstance(owner, pt.PlantumlActor):
                    color = "#C6E6FF"
                #owner_path = owner.path # sanitize_name(owner.name)
                participants[owner.path] = f'  participant "{owner.name}" as {owner.path} {color}'
        self.participants = participants

    def set_simulation_decorator(self, deco_text):
        self.sequence.append(deco_text)

    def set_simulation_activate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = component.owner.ref # self.architecture.get_activity_owner(component)
        self.part_seq.append(component.path)
        self.sequence.append(f"  activate {component.path}")

    def set_simulation_deactivate(self, component):
        if isinstance(component, pt.PlantumlActivity):
            component = component.owner.ref # self.architecture.get_activity_owner(component)
        self.sequence.append(f"  deactivate {component.path}")

    def set_simulation_activity_decorator(self, component):
        if not isinstance(component, pt.PlantumlActivity):
            return
        owner = self.architecture.get_activity_owner(component)
        owner2 = self.architecture.get_owner(component)
        
        #print(f"  Owner = {component.name} {component.owner} {component.owner.ref} {owner.path} {owner2.path}")
        self.part_seq.append(component.owner.ref.path)
        self.sequence.append(f"  rnote over {component.owner.ref.path} #C5FFA6\n{component.name}\n  endrnote")

    def set_simulation_state_decorator(self, component, state_str):
        if not isinstance(component, pt.PlantumlActivity):
            return
        owner = self.architecture.get_activity_owner(component)
        owner2 = self.architecture.get_owner(component)
        
        #print(f"  Owner = {component.name} {component.owner} {component.owner.ref} {owner.path} {owner2.path}")
        self.part_seq.append(component.owner.ref.path)
        self.sequence.append(f"  hnote over {component.owner.ref.path} #C6E6FF\n{state_str}\n  endrnote")
        
    def set_simulation_note_decorator(self, component, note_str):
        if not isinstance(component, pt.PlantumlActivity):
            return
        owner = self.architecture.get_activity_owner(component)
        owner2 = self.architecture.get_owner(component)
        
        #print(f"  Owner = {component.name} {component.owner} {component.owner.ref} {owner.path} {owner2.path}")
        self.part_seq.append(component.owner.ref.path)
        self.sequence.append(f"  note over {component.owner.ref.path}\n{note_str}\n  endrnote")

    async def run(self, activities):
        # Run the list of coroutines concurrently
        await asyncio.gather(*(coro.run(self) for coro in activities))

    def simulate(self):
        activities = self.architecture.get_all_activities()
        self.part_seq = [] # clear part_seq from previous simulation
        self.sequence = [] # clear sequence
        self.queues = {}   # clear queues

        # Add some priority participant to the sequence in the diagram.
        self.part_seq += self.metadata_dict["comp_order"]
        
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
        
        # Only shows participants that where really used in the simulation
        # Use list instead of set to preserve order
        for item in self.part_seq:
            if not item in new_list_of_participants:
                new_list_of_participants.append(item)
        
        print("")            
        # Show participants
        for item in new_list_of_participants:
            print(self.participants[item])
        print("")            
        
        # Show sequences
        for item in self.sequence :
            print(item)
            print("")            
        
        print("@enduml")            

    def get_queue(self, connection):
        # print(f"   -----> get_queue connection = {connection}")
    
        if isinstance(connection, pt.ObjectRef):
            connection = connection.ref
        # print(f"   -----> get_queue connection name = {connection}")
            
        if not connection.name in self.queues:
            self.queues[connection.name] = asyncio.Queue()
        return self.queues[connection.name]

    def print_transmission(self, connection, sender, text):
        send_path = sender.path 
        if isinstance(sender, pt.PlantumlActivity):
            send_path = sender.owner.ref.path 
            
        if isinstance(connection, pt.ObjectRef): # Maybe unecessary, to check
            connection = connection.ref

        other = connection.comp2
        # other = connection.comp2.ref
        # if other == sender:
            # other = connection.comp1.ref
            
        # It can be a list of trasmission refs or a single transmission ref.
        # To simplify, treat all as list
        if isinstance(other, list):
            # This happens only in case send 1 to multiple
            destinations = other
        else:
            # This can happen bedirectionaly
            if other.ref == sender:
                other = connection.comp1
            destinations = [other]
            
        for dest in destinations:
            other_path = dest.ref.path
            
            if isinstance(dest.ref, pt.PlantumlActivity):
                other_path = dest.ref.owner.ref.path 
            self.part_seq.append(send_path)
            self.part_seq.append(other_path)
            self.sequence.append(f"{send_path} -> {other_path}: {text}")
        
    async def send_message(self, connection, sender, lable, data=""):
        """
        Sends a message to the queue (or to multiple output queues of the connection).
        This method also yields the control to the event loop after sending.
        """
        if connection == None:
            return
        if sender == None:
            return
        if lable == None:
            return
        self.print_transmission(connection, sender, lable)
        
        queue = self.get_queue(connection)
        if isinstance(queue, list):
            for queue_item in queue:
                await self.get_queue(connection).put({"label":lable, "data":data})
        else:
            await self.get_queue(connection).put({"label":lable, "data":data})

    async def send_message_and_wait(self, connection, sender, lable, data=""):
        """
        Sends a message and waits for an answer in the bedirectional queue.
        """
        if connection == None:
            return
        if sender == None:
            return
        if lable == None:
            return
        self.print_transmission(connection, sender, lable)
        self.get_queue(connection).put_nowait({"label":lable, "data":data})
        item = await self.get_queue(connection).get()
        return item

    async def wait_message(self, connection):
        """
        Waits for a message in the queue (or multiple input queues).
        """
        if connection == None:
            return
        item = await self.get_queue(connection).get()
        return item
