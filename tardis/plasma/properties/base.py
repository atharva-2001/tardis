import logging

from abc import ABCMeta, abstractmethod, abstractproperty
import numpy as np
import pandas as pd

__all__ = ['BasePlasmaProperty', 'BaseAtomicDataProperty',
           'HiddenPlasmaProperty', 'Input', 'ArrayInput', 'DataFrameInput',
           'ProcessingPlasmaProperty', 'PreviousIterationProperty']

logger = logging.getLogger(__name__)

class BasePlasmaProperty(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def outputs(self):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    def __init__(self):
        for output in self.outputs:
            setattr(self, output, None)

    def _update_type_str(self):
        """
        Get type string for Label

        Returns
        -------
            : ~str

        """
        self.type_str = repr(type(self.value))


    def get_latex_label(self):
        latex_template = r"""\textbf{{Name}} {name}
\textbf{{Formula}} {formula}
{description}
"""
        outputs = self.outputs.replace('_', r'\_')
        latex_name = getattr(self, 'latex_name', '')
        if latex_name != '':
            complete_name = '{0} [{1}]'.format(latex_name, self.latex_name)
        else:
            complete_name = latex_name

        latex_label = latex_template.format(name=complete_name,
                                     formula=getattr(self,
                                                     'latex_formula', '--'),
                                     description=getattr(self,
                                                         'latex_description',
                                                         ''))
        return latex_label.replace('\\', r'\\')

class ProcessingPlasmaProperty(BasePlasmaProperty):
    __metaclass__ = ABCMeta

    def __init__(self, plasma_parent):
        super(ProcessingPlasmaProperty, self).__init__()
        self.plasma_parent = plasma_parent
        self._update_inputs()

    def _update_inputs(self):
        """
        This function uses the CPython API to read the variable names from the
        `calculate`-function and makes the plasma routines easily programmable.
        """
        calculate_call_signature = self.calculate.func_code.co_varnames[
                                   :self.calculate.func_code.co_argcount]
        self.inputs = [item for item in calculate_call_signature if
                      item != 'self']


    def _get_input_values(self):
        return (self.plasma_parent.get_value(item) for item in self.inputs)

    def update(self):
        """
        Updates the processing Plasma by calling the `calculate`-method with
        the required inputs

        :return:
        """
        if len(self.outputs) == 1:
            setattr(self, self.outputs[0], self.calculate(
                *self._get_input_values()))
        else:
            new_values = self.calculate(*self._get_input_values())
            for i, output in enumerate(self.outputs):
                setattr(self, output, new_values[i])

    @abstractmethod
    def calculate(self, *args, **kwargs):
        raise NotImplementedError('This method needs to be implemented by '
                                  'processing plasma modules')

class HiddenPlasmaProperty(ProcessingPlasmaProperty):
    __metaclass__ = ABCMeta

    def __init__(self, plasma_parent):
        super(HiddenPlasmaProperty, self).__init__(plasma_parent)

class BaseAtomicDataProperty(ProcessingPlasmaProperty):
    __metaclass__ = ABCMeta

    inputs = ['atomic_data', 'selected_atoms']

    def __init__(self, plasma_parent):

        super(BaseAtomicDataProperty, self).__init__(plasma_parent)
        self.value = None

    @abstractmethod
    def _set_index(self, raw_atomic_property):
        raise NotImplementedError('Needs to be implemented in subclasses')

    @abstractmethod
    def _filter_atomic_property(self, raw_atomic_property):
        raise NotImplementedError('Needs to be implemented in subclasses')

    def calculate(self, atomic_data, selected_atoms):

        if getattr(self, self.outputs[0]) is not None:
            return getattr(self, self.outputs[0])
        else:
# Atomic Data Issue: Some atomic property names in the h5 files are preceded
# by an underscore, e.g. _levels, _lines.
            try:
                raw_atomic_property = getattr(atomic_data, '_'
                                              + self.outputs[0])
            except AttributeError:
                raw_atomic_property = getattr(atomic_data, self.outputs[0])
            finally:
                return self._set_index(self._filter_atomic_property(
                    raw_atomic_property, selected_atoms))

class Input(BasePlasmaProperty):

    def _set_output_value(self, output, value):
        setattr(self, output, value)

    def set_value(self, value):
        assert len(self.outputs) == 1
        self._set_output_value(self.outputs[0], value)

class ArrayInput(Input):
    def _set_output_value(self, output, value):
        setattr(self, output, np.array(value, copy=False))

class DataFrameInput(Input):
    def _set_output_value(self, output, value):
        setattr(self, output, np.array(pd.DataFrame(value), copy=False))

class PreviousIterationProperty(BasePlasmaProperty):

    def _set_initial_value(self, value):
        self.set_value(value)

    def _set_output_value(self, output, value):
        setattr(self, output, value)

    def set_value(self, value):
        assert len(self.outputs) == 1
        self._set_output_value(self.outputs[0], value)
