
from . import base_runner


class Builder(base_runner.BaseBuilder):

    def create_diagram_code(self, diagram):

        self.inits = ""
        self.processes = ""

        self.processes += "\n\t" "while True:"
        self.inits += "\n\n" "def {}():".format(diagram.name)
        self._merge_component_code(diagram)

        self.inits += '\n\t' + self._build_yield(diagram, enable_output=False)
        self.processes += '\n\t\t' + self._build_yield(diagram) + self._generate_executor_str(diagram)

        return self.inits + self.processes + '\n\n'

    @staticmethod
    def _build_yield(diagram, enable_output=True):

        yield_str = 'yield '
        if len(diagram.inputs) != 0:
            yield_str = ', '.join(input_.name for input_ in diagram.inputs.sort()) + ' = ' + yield_str
        if enable_output and len(diagram.outputs) != 0:
            yield_str += '{' + ', '.join('"{0}": {0}'.format(output.name) for output in diagram.outputs.sort()) + '}'
        return yield_str

    def _merge_component_code(self, system):

        for comp in system.organizer.ordered_comps:
            if comp.code_str["Set Up"] is not None:  # Build Set Up
                self.inits += "\n\t" + comp.code_str['Set Up'].replace('\t', '\t\t')
            if comp.code_str["Execution"] is not None:  # Build process
                self.processes += '\n\t\t' + comp.code_str['Execution'].replace('\t', '\t\t')
            if comp.is_system():  # Get code from subsystem
                self._merge_component_code(comp)

    @staticmethod
    def _generate_executor_str(diagram):

        return '\n\n\n' + '{0}_exec = {1}.Executor("{0}", {0}(), '.format(diagram.name, diagram.runner_name) + \
                        str([str(comp) for comp in diagram.inputs.sort()]) + ')'


class Executor(base_runner.BaseExecutor):

    def __init__(self, name, evaluators, input_order):

        super(Executor, self).__init__(name, evaluators)

        next(self.evaluators)  # Initialize system
        self.input_order = input_order  # Order in which the inputs are entered in the system

    def run(self, inputs=None):

        if inputs is None:  # This is for systems that do not have any inputs
            return self.evaluators.send(None)
        sys_inputs = [inputs[var] for var in self.input_order]  # Pass inputs in the order the system requires it
        return self.evaluators.send(sys_inputs)


class Organizer(base_runner.BaseOrganizer):

    def map_component(self, comp):

        self.ordered_comps.append(comp)
