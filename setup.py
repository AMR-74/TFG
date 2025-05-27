from setuptools import setup, find_packages

setup(
    name='tfg',  # Nombre de tu proyecto (lo que luego usarás para importar)
    version='0.1',
    packages=find_packages(),  # Encuentra automáticamente los paquetes que tienen __init__.py
    include_package_data=True,
    install_requires=[
        'Django>=4.2', 
        'pymongo',
        'asgiref',
        'dnspython',
        'pip >= 25.0.1',
        'sqlparse',
        'tzdata'
        # Aquí pones otras dependencias necesarias
    ],
)