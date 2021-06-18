from distutils.core import setup
setup(
  name = 'robyn',         # How you named your package folder (MyLib)
  packages = ['robyn'],   # Chose the same as "name"
  version = '0.2.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'An async python framework with the backend runtime written in rust.',   # Give a short description about your library
  author = 'SANSKAR JETHI',                   # Type in your name
  url = 'https://github.com/sansyrox/robyn',   # Provide either the link to your github or to your website
  # download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['python', 'rust', 'pyo3', 'async'],   # Keywords that define your package best
  # install_requires=[            # I get to this in a second
  #         'validators',
  #         'beautifulsoup4',
  #     ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
