import os

from m2cgen import ast
from m2cgen.interpreters import mixins, utils
from m2cgen.interpreters.haskell.code_generator import HaskellCodeGenerator
from m2cgen.interpreters.interpreter import ToCodeInterpreter


class HaskellInterpreter(ToCodeInterpreter,
                         mixins.LinearAlgebraMixin):
    supported_bin_vector_ops = {
        ast.BinNumOpType.ADD: "addVectors",
    }

    supported_bin_vector_num_ops = {
        ast.BinNumOpType.MUL: "mulVectorNumber",
    }

    exponent_function_name = "exp"
    tanh_function_name = "tanh"

    def __init__(self,  module_name="Model", indent=4, function_name="score",
                 *args, **kwargs):
        self.module_name = module_name
        self.function_name = function_name

        cg = HaskellCodeGenerator(indent=indent)
        super(HaskellInterpreter, self).__init__(cg, *args, **kwargs)

    def interpret(self, expr):
        self._cg.reset_state()
        self._reset_reused_expr_cache()

        self._cg.add_code_line(self._cg.tpl_module_definition(
            module_name=self.module_name))

        args = [(True, self._feature_array_name)]
        func_name = self.function_name

        with self._cg.function_definition(
                name=func_name,
                args=args,
                is_scalar_output=expr.output_size == 1):
            last_result = self._do_interpret(expr)
            self._cg.add_code_line(last_result)

        if self.with_linear_algebra:
            filename = os.path.join(
                os.path.dirname(__file__), "linear_algebra.hs")
            self._cg.prepend_code_lines(utils.get_file_content(filename))

        return self._cg.code

    def interpret_pow_expr(self, expr, **kwargs):
        base_result = self._do_interpret(expr.base_expr, **kwargs)
        exp_result = self._do_interpret(expr.exp_expr, **kwargs)
        return self._cg.infix_expression(
            left=base_result, right=exp_result, op="**")
