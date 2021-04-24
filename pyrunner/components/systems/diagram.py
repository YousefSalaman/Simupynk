__all__ = ["BlockDiagram"]

import re
from functools import wraps

from ..base_comp import *
from .base_sys import BaseSystem
from ...utils.file_find import find_module


# BlockDiagram definition and helpers


def _shiftmethod(func):
    """Decorator that enables component name shifting.

    This is done by finding the components that share the same basename as the
    component being used as a reference. Every time one of these components is
    found, the wrapped shift function is called to rename the similarly named
    component, if necessary.
    """

    @wraps(func)
    def method_wrapper(diagram, comp: BaseComponent, comp_name=None):

        # Get component attributes
        if comp_name is None:
            basename, name_index = _NameManager.get_name_attrs(comp.name)
        else:
            basename, name_index = _NameManager.get_name_attrs(comp_name)

        # Perform shifting with wrapped function
        basename_count = diagram._name_mgr.get_name_count(basename)  # Gets registered count for the basename
        similar_comps = diagram.search_component_name(basename)  # List components with similar names
        for similar_comp in similar_comps:
            _, similar_name_index = _NameManager.get_name_attrs(similar_comp.name)
            similar_name_match = similar_comp is not comp \
                                 and basename_count > similar_name_index \
                                 and re.match(basename + '(_[1-9][0-9]*)?', similar_comp.name)

            if similar_name_match:
                func(diagram, basename, name_index, similar_comp, similar_name_index)

    return method_wrapper


class BlockDiagram(BaseSystem):
    """The component that acts as the main container for all other components.

    Every component, that is not a BlockDiagram component, must be contained
    either directly in one of these objects or in another system component that
    is also contained in a BlockDiagram component.

    It functions as a "component manager" in the sense that it can manipulate
    the properties of the components contained within it. It can do the
    following:

    - It can register or unregister component names to its internal name
      registry.

    - It builds the different components by organizing and generating the 
      code to run the system. To do this, the system uses a runner module,
      which contains the instructions on how to do these tasks.
      
    - It can remove or add any components to the system (except another diagram
      object.)
    """

    _DIAGRAMS = []  # List to store diagram objects

    default_name = generate_default_name("")

    direct_feedthrough = generate_direct_feedthrough(False)

    input_info = generate_input_info(None)

    output_info = generate_output_info(None)

    parameter_info = generate_parameter_info(None)

    def __init__(self, name: str, runner_name: str):

        try:
            self.diagram = self  # State you're the diagram for your subsystems
            self._name_mgr = _NameManager()  # A "namespace" to register components
            self.runner = find_module(runner_name, "runners")

            self._DIAGRAMS.append(self)  # Register diagram in class

        except TypeError as e:
            raise TypeError("The arguments name and runner_name must be strings") from e

        super().__init__(self, name)

    def build(self):
        """Builds up the BlockDiagram object.

        This method will do the following to accomplish this:

        - Verify the properties for each component in the system follows the
          criteria established by each component, respectively.

        - It will determine in what order the system will execute each
          component.

        - Pass the default parameters to its respective components.

        - It will generate the code string for the system.
        """

        self.pass_default_parameters()
        self.verify_properties()
        self.organize()
        self.generate_code_string()

    @classmethod
    def build_diagrams(cls):
        """Build all BlockDiagram objects within a script."""

        for diagram in cls._DIAGRAMS:
            diagram.build()

    def clear_diagram(self):
        """Remove all the components directly in the block diagram.

        The method will only remove the items that are directly on the
        BlockDiagram's component list. However, it will unregister every
        component name in the BlockDiagram component to leave the name
        registry empty.
        """

        for comp in self.comps.copy():
            if comp.is_system():
                comp.unregister_all_components()
            self.unregister_component_name(comp)
            self.remove_component(comp)

    def register_component_name(self, comp: BaseComponent, name: str) -> str:
        """Remove component's name from the name registry.

        When registering a name, the system will do one of two things:

        - If a custom name was entered, the name registry checks if the name
          was previously entered. If it the name is indexed (i.e., the name
          ends with "_i", where i is a positive integer), then the registry
          will raise an error. Otherwise, it will register it as normal.

        - If a custom name was not entered, the name is generated by the
          component and it is registered in the name registry.
        """

        if name is None:
            return self._name_mgr.register_name(comp.generate_name())

        self._name_mgr.register_custom_name(name)
        if self._name_mgr.get_name_count(name) > 1:  # Perform right shift if custom name is not unique
            self._shift_component_names_right(comp, name)
        return name

    def remove_components(self, *comps: BaseComponent):
        """Remove a collection of components from the system.

        The component(s) can directly be in the BlockDiagram object or they can
        reside in a system component within the BlockDiagram object.
        """

        for comp in comps:
            self.unregister_component_name(comp)
            self.remove_component(comp)

    def unregister_component_name(self, comp: BaseComponent):
        """Unregister a component from the block diagram's name registry.

        After unregistering the component's name, the code will verify if the
        name was generated by the name register and the diagram will shift the
        component names that were generated afterward to the left by renaming
        the components using the base name and name index.

        Although this method is public, it should be used with caution since
        this will rename the components that use the same base name. Only use
        this when you are going to remove a component from the block diagram.
        """

        if self._name_mgr.is_name_registered(comp.name):
            self._shift_component_names_left(comp)
            self._name_mgr.unregister_name(comp.name)

    @_shiftmethod
    def _shift_component_names_left(self, basename, name_index, similar_comp, similar_name_index):
        """Shift component names to the left."""

        if similar_name_index > name_index:
            if similar_name_index == 1:
                similar_comp.name = basename
            else:
                similar_comp.name = basename + '_' + str(similar_name_index - 1)

    @_shiftmethod
    def _shift_component_names_right(self, basename, name_index, similar_comp, similar_name_index):
        """Shift component names to the right"""

        if similar_name_index >= name_index:
            similar_comp.name = basename + '_' + str(similar_name_index + 1)


# Name manager definition

class _NameManager:
    """A class that behaves like a namespace for BlockDiagram objects.

    It keep tracks of the variables being registered or unregistered in the
    system by using name registry that is stored within a NameManager object.
    The purpose of this class is to ensure every component inside a diagram
    gets a unique name, so calculations can be done correctly.

    There are two ways a name can be registered in the name registry:

    - Explicit: This happens when the name appears as an entry in the registry
      and the internal name count is one. When a name is entered for the first
      time in the registry, a name is always explicitly registered.

    - Implicit: This happens when the name appears as a key in the registry and
      the internal count is higher than one. Instead of making a new entry in
      the registry, the registry counts the amount of times the name has been
      registered and uses that to create a new name. In other words, when a
      name is entered, the count for that name is increased by one (i.e. the
      name registry is updated.) A name is implicitly registered after it has
      been explicitly registered once with the same name (or basename.)

    A valid name that can be registered in this class has the following
    pattern:

                valid_name = basename + _ + registry index

    where the basename is everything else that is not the "_" + index and the
    registry index is a number given to a name when it is implicitly registered
    in the name registry.
    """

    def __init__(self):

        self._registry = {}  # Name registry for a BlockDiagram object

    @staticmethod
    def get_name_attrs(name: str):
        """Get a name's basename and index."""

        try:
            basename, name_index, _ = re.split("(_[1-9][0-9]*)+$", name)
            name_index = int(name_index.split('_')[1])
        except ValueError:  # This only happens if there's no index at the end
            name_index = 0
            basename = name

        return basename, name_index

    def get_name_count(self, name: str):
        """Get the amount of times a name has been registered.
        
        It return None if the key is invalid."""

        if name in self._registry:  # If name is explicitly registered
            return self._registry[name]

        if self._is_implicitly_registered(name):
            basename, _ = self.get_name_attrs(name)
            return self._registry[basename]

        return  # Otherwise, return nothing

    def is_name_registered(self, name: str):
        """Verify if name is registered in the name registry."""

        if name in self._registry:  # Check for explicit registration
            return True

        # Check if the name has the generated name format and then check for
        # implicit registration
        if re.search("(_[1-9][0-9]*)+$", name):
            return self._is_implicitly_registered(name)

        return False  # Otherwise, it's not there

    def register_custom_name(self, name: str):
        """Register a custom name.

        Three things can happen when using this method:

        - If the name was already explicitly registered and it has an index,
          then the code will raise an error for trying to enter a duplicate
          custom name.

        - If the name is implicitly registered, then it will just update the
          name registry and generate a new name based on that

        - Otherwise, the component's name is registered as is and returns the
          name the same way it was entered.
        """

        if re.search("(_[1-9][0-9]*)+$", name):  # Verify if name has indexed format

            # Check if name is already explicitly registered
            if name in self._registry:
                raise NameError("No duplicate names with indexes, like 'vars_1', are not allowed "
                                "as a custom name.")

            # Check if name is implicitly registered and register if it is
            if self._is_implicitly_registered(name):
                basename, _ = self.get_name_attrs(name)
                self.register_name(basename)
                return name

        return self.register_name(name)  # Otherwise, explicitly register name

    def register_name(self, name: str) -> str:
        """Register a name explicitly or implicitly.

        In case a name that is implicitly registered, but the new generated
        name clashes with a name that has been previously entered, then the
        explicitly registered name is will be unregistered. In other words, the
        entry under that name will be deleted since it is implicitly registered
        in the name registry, so there is no need for the same name to appear
        in the registry as a key.
        """

        if name in self._registry:  # Update name registry (i.e. implicitly register name)
            while True:
                new_name = name + "_" + str(self._registry[name])
                self._registry[name] += 1
                if new_name in self._registry:  # There's an explicitly registered name that clashes with the new name
                    self.unregister_name(new_name)
                else:
                    return new_name

        # Register name for the first time (i.e. explicitly register name)
        self._registry[name] = 1
        return name

    def unregister_name(self, name):
        """Unregister a component name from the name registry.

        Three things can happen when using this method:

        - If the component's name is found in the name registry, then it is
          unregistered.

        - If the component's basename is found in the name registry, then the
          basename is unregistered instead.

        - Otherwise, it will count as an invalid name entry was going to be
          deleted and raises a NameError.
        """

        # It's a custom name or the default name of a component (i.e. its "base name")
        if name in self._registry:
            self._unregister_name(name)

        # It's a generated name or it's a custom name that matches the name generation format
        elif re.search("(_[1-9][0-9]*)+$", name):
            basename, _ = self.get_name_attrs(name)
            if basename in self._registry:
                self._unregister_name(basename)

        # An invalid name was entered
        else:
            raise NameError(f"Component name {name} was not found in name registry.")

    def _is_implicitly_registered(self, name: str) -> bool:
        """Verify if name is implicitly registered in the name registry.

        This is done by checking if the basename is in the registry and if the
        name's index is within the amount of generated entries in the registry
        that use the same basename.
        """

        basename, name_index = self.get_name_attrs(name)
        return basename in self._registry and name_index < self._registry[basename]

    def _unregister_name(self, name: str):

        name_cnt = self._registry[name]  # Amount of times the name has been registered
        if name_cnt == 1:
            del self._registry[name]
        elif name_cnt > 1:
            self._registry[name] -= 1