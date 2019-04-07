import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='shoedog',
     version='0.0.1',
     scripts=[] ,
     author="Jay Chia",
     author_email="jaychia04@gmail.com",
     description="A search tool built on SQLAlchemy",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/jaychia/shoedog",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3.6",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
