exists() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "$1 is installed."
    return 0
  else
    echo "$1 is not installed."
    return 1
  fi
}
pytest
#abort if not all tests pass
if [ $? -ne 0 ]; then
  echo "Tests must pass before uploading to PyPI"
  exit 1
fi
current_version=$(grep "version = " pyproject.toml | sed 's/version = //g' | sed 's/"//g' | sed 's/ //g')
echo "Current version: $current_version"
bumped_version=$(python3 -c "print('$current_version'.split('.')[0] + '.' + '$current_version'.split('.')[1] + '.' + str(int('$current_version'.split('.')[2]) + 1))")
echo "Bumped version: $bumped_version"
sed -i '' "s/version = \"$current_version\"/version = \"$bumped_version\"/g" pyproject.toml
if ( exists op ); then
  api_token=$(op item get "pypi api key" --field "Anmeldedaten")
else
  api_token=$(read -s -p "Enter your PyPI API token: ")
fi
python3 -m pip install --upgrade twine
python3 -m pip install --upgrade build
rm -rf dist/*
python3 -m build
confirmation=$(read -p "Do you want to upload the new version to PyPI? (y/n) " -n 1 -r)
echo "Uploading to PyPI"
python3 -m twine upload --repository pypi dist/* --user __token__ --password $api_token
pip install --upgrade $(basename $(pwd))