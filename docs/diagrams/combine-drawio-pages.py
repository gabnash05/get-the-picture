from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

path = Path(__file__).with_name('generate-diagrams.py')
spec = spec_from_file_location('drawing_game_diagrams', path)
module = module_from_spec(spec)
spec.loader.exec_module(module)
module.combine_pages()
