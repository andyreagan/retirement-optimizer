Thoroughly research the issue in the codebase.

This app is Svelte frontend and Django backend.
Run the app by (1) compiling the frontend via ./build_frontend.sh and (2) cd backend && python manage.py migrate.
You can query the API, curl the frontend, or use playright to hit the front end directly.

After making a change, both the front and backend tests must be run and updated if necessary.
You can see how to run them in the Makefile.
If this functionality is not tested, add a test!

Create a branch and make a commit describing the changes.
Make a pull request against main on the branch in github.
