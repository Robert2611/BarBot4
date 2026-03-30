import shutil
from pathlib import Path
from platformdirs import user_config_dir

def main():
    data_folder = Path(user_config_dir("barbot"))
    log_folder = data_folder / "log"
    recipes_folder = data_folder / "recipes"
    package_recipes_folder = Path(__file__).parent.parent / "recipe-collections" / "standard"

    print(f"Creating data folders in {data_folder}...")
    log_folder.mkdir(parents=True, exist_ok=True)
    recipes_folder.mkdir(parents=True, exist_ok=True)

    print(f"Copying recipes from {package_recipes_folder} to {recipes_folder}...")
    if package_recipes_folder.exists():
        for item in package_recipes_folder.iterdir():
            dest = recipes_folder / item.name
            if not dest.exists():
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    shutil.copytree(item, dest)
    else:
        print(f"Warning: No recipes found in {package_recipes_folder}")

    print("Setup complete!")

if __name__ == "__main__":
    main()
