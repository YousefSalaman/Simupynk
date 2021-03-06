
__all__ = ["BaseBuilder",
           "BaseExecutor",
           "BaseOrganizer"]


import os
import re
from abc import abstractmethod

from . import executors
from ..utils.type_abc import TypeABC


class BaseExecutor(TypeABC):
    """Base class for executor objects."""

    def __init__(self, name, evaluators):

        self.evaluators = evaluators  # Object(s) that are used to run the system

        executors.add(name, self)  # Store executor

    @abstractmethod
    def run(self, inputs=None):
        pass


class BaseBuilder(TypeABC):

    def __init__(self):

        self.inits = None  # Attribute to store initialization code
        self.processes = None  # Attribute to store process code

    @classmethod
    def create_code(cls, diagrams, file_path=None, namespace=None):

        code = cls._create_code_string(diagrams)
        if file_path is None:
            if namespace is None:
                namespace = globals()
            exec(code, namespace)
        else:
            cls._create_script(file_path, code)

    @abstractmethod
    def create_diagram_code(self, diagram):
        """Gather different parts from the components in diagram to create and
        return the code.
        """

    @staticmethod
    def _create_code_string(diagrams):

        code = ''
        imports = ''
        all_imports = set()
        for diagram in diagrams:
            builder = diagram.runner.Builder()
            code += builder.create_diagram_code(diagram)
            imports += builder._create_imports(diagram, all_imports)

        return imports + code

    @staticmethod
    def _create_imports(diagram, all_imports):

        imports = ""
        for lib_name, alt_name in diagram.lib_deps.items():
            if lib_name not in all_imports:
                all_imports.add(lib_name)
                imports += "import " + lib_name
                if alt_name is not None:
                    imports += " as " + alt_name
                imports += "\n"

        return imports

    @staticmethod
    def _create_script(file_path, code):

        dir_path, filename = os.path.split(file_path)
        if not os.path.isdir(dir_path):
            raise OSError("The path that was given is not a valid directory")
        if not re.match("^[_a-zA-Z][_a-zA-Z0-9]+\.py$", filename):
            raise NameError("The filename must be a valid python filename.")

        # Create script with the generated code
        with open(file_path, mode="w") as script:
            script.write(code)

    @staticmethod
    @abstractmethod
    def _generate_executor_str(diagram):
        """Generate the line that initializes the executor."""


class BaseOrganizer(TypeABC):
    """Base class for organizer objects"""

    def __init__(self):

        self.sys_info = None
        self._sys_trail = []   # Store components in trail to detect if the system is cyclic (has a feedback loop)
        self.ordered_comps = []

    @abstractmethod
    def map_component(self, comp):
        """
        Determine where a component should be in its system order of
        execution based on the criteria established by this method.
        """

    def define_sys_info(self, comps):
        """
        Create a dictionary to hold relevant information of each component of
        the system. This is used to define some attributes of the organizer
        object for code generation.

        Sys info is a dictionary with the following structure:

        - As keys, it has the system's components.

        - As values, it has dictionaries with additional information of the
          component. By default, the dictionary contains an entry with
          key = 'inputs' and value = list of the components inputs. This is the
          only one that is used in the traversal process of the system.

        The diagram below shows the structure of the dictionary:

        {
            comp_1 : {'inputs': [...], ...},
            .
            .
            .
            comp_n : {'inputs': [...], ...}
        }

        To add any additional entries to each sub-dictionary, just override
        this method, update the resulting dictionary, and return it.
        """

        sys_info = {}
        for comp in comps:
            sys_info[comp] = {'inputs': [value for value in comp.inputs.values() if value is not None]}
        self.sys_info = sys_info

    def build_system_order(self, comp):

        self._sys_trail.append(comp)  # Record component in the trail

        comp_inputs = self.sys_info[comp]['inputs']
        for input_comp in comp_inputs:
            if input_comp in self._sys_trail:  # There's a feedback loop in your system (system is cyclic)
                self._sever_system_loop(input_comp)
            if input_comp.is_not_mapped:
                self.build_system_order(input_comp)

        if comp.is_not_mapped:
            self.map_component(comp)
            comp.is_not_mapped = False
            if comp in self._sys_trail:  # Remove component from trail after finishing
                self._sys_trail.remove(comp)

    def _sever_system_loop(self, comp):
        """
        Split the system loop by removing the input component to a component
        that is non-direct feedthrough, where both components are within the
        loop.
        """

        non_direct_comp, loop_input_comp = self._get_loop_components(comp)
        self.sys_info[non_direct_comp]['inputs'].remove(loop_input_comp)

        self._sys_trail.clear()

    def _get_loop_components(self, comp):
        """
        Gets non-direct feedthrough component and its input component in the
        loop.
        """

        input_index = self._sys_trail.index(comp)
        sys_loop = self._sys_trail[input_index:]  # Gets the loop portion in the recorded trail

        for loop_comp_index, loop_comp in enumerate(sys_loop):
            loop_input_comp = self._get_component_input_in_loop(loop_comp_index, sys_loop)
            if not loop_input_comp.direct_feedthrough:
                return loop_comp, loop_input_comp

        raise Exception("System cannot process algebraic loops. There needs to be "
                        "a non-direct feedthrough component in your feedback loop.")

    @staticmethod
    def _get_component_input_in_loop(loop_comp_index, sys_loop):
        """Get loop component's input within a system loop."""

        try:  # Normally, next element in sys_loop is the input
            return sys_loop[loop_comp_index + 1]
        except IndexError:  # If loop_comp is the last element, its input is first comp in sys_loop
            return sys_loop[0]
