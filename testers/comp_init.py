import Simupynk.components as comps
from Simupynk.components.systems import BaseInnerSystem


INPUT_INFO = (
    {"test", "test1", "test2"},  # Required inputs properties
    {"test", "test1", "test2", "test3"}  # All input properties
)

OUTPUT_INFO = (
    {"result", "result1"},  # Required outputs properties
    {"result", "result1", "result2"}  # All output properties
)

PARAMETER_INFO = (
    {"para", "para1"},  # Required parameters
    {"para", "para1", "para2"}  # All parameters
)


class InitCompVariant(comps.BaseComponent):

    has_init_cond = comps.generate_has_init_cond(True)

    input_info = comps.generate_input_info(INPUT_INFO)

    output_info = comps.generate_output_info(OUTPUT_INFO)

    parameter_info = comps.generate_parameter_info(PARAMETER_INFO)

    default_name = comps.generate_default_name("test_var")

    def generate_component_string(self):

        print("Just a test")
        super().generate_component_string()


class InitCompInvariant(comps.BaseComponent):

    has_init_cond = comps.generate_has_init_cond(True)

    input_info = comps.generate_input_info(None)

    output_info = comps.generate_output_info(None)

    parameter_info = comps.generate_parameter_info(None)

    default_name = comps.generate_default_name("test_inv")

    def generate_component_string(self):

        print("Just a test")
        super().generate_component_string()


class InitCompSystem(BaseInnerSystem):

    has_init_cond = comps.generate_has_init_cond(True)

    input_info = comps.generate_input_info(None)

    output_info = comps.generate_output_info(None)

    parameter_info = comps.generate_parameter_info(None)

    default_name = comps.generate_default_name("System")

    def generate_component_string(self):

        print("Just a test")
        super().generate_component_string()