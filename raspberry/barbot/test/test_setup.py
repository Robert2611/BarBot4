import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from barbot.setup import main

@pytest.fixture
def mock_fs():
    with patch("barbot.setup.Path") as mock_path, \
         patch("barbot.setup.shutil") as mock_shutil, \
         patch("barbot.setup.user_config_dir") as mock_conf_dir:
        
        mock_conf_dir.return_value = "/tmp/barbot"
        
        # Mock Path objects
        data_folder = MagicMock(spec=Path)
        log_folder = MagicMock(spec=Path)
        recipes_folder = MagicMock(spec=Path)
        package_recipes_folder = MagicMock(spec=Path)
        
        # Path constructor behavior
        def path_side_effect(*args):
            if str(args[0]) == "/tmp/barbot":
                return data_folder
            # Handle Path(__file__).parent / "data" / "recipes"
            return MagicMock(spec=Path)
        
        mock_path.side_effect = path_side_effect
        
        # Handle division operator for Path
        data_folder.__truediv__.side_effect = lambda x: log_folder if x == "log" else recipes_folder
        
        # Mock iterdir for package recipes
        mock_item = MagicMock(spec=Path)
        mock_item.name = "mock_recipe.json"
        mock_item.is_file.return_value = True
        package_recipes_folder.iterdir.return_value = [mock_item]
        package_recipes_folder.exists.return_value = True
        
        yield {
            "data_folder": data_folder,
            "log_folder": log_folder,
            "recipes_folder": recipes_folder,
            "package_recipes_folder": package_recipes_folder,
            "shutil": mock_shutil,
            "mock_path": mock_path
        }

def test_setup_main(mock_fs):
    # Set recipe package path behavior
    package_dir = mock_fs["package_recipes_folder"]
    package_dir.exists.return_value = True
    
    mock_item = MagicMock(spec=Path)
    mock_item.name = "mock_recipe.json"
    mock_item.is_file.return_value = True
    package_dir.iterdir.return_value = [mock_item]
    
    # Set destination path behavior
    dest_recipe = MagicMock(spec=Path)
    dest_recipe.exists.return_value = False
    mock_fs["recipes_folder"].__truediv__.return_value = dest_recipe
    
    # We need to ensure that Path(__file__).parent / "data" / "recipes" returns our mock
    # Path() in setup.py is mocked to return data_folder by default in fixture or another mock
    # Let's simplify and just patch Path globally within the function call
    with patch("barbot.setup.Path") as mock_path_class:
        # Path(user_config_dir("barbot"))
        mock_path_class.return_value = mock_fs["data_folder"]
        # Path(__file__)
        mock_path_class.return_value.parent.__truediv__.return_value.__truediv__.return_value = package_dir
        
        main()
        
        mock_fs["log_folder"].mkdir.assert_called()
        mock_fs["recipes_folder"].mkdir.assert_called()
        mock_fs["shutil"].copy2.assert_called()
