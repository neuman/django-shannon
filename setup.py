from distutils.core import setup
setup(
    name = 'django-shannon',
    packages = ['shannon'],
    version = '1.0.3',
    description='S3 backed django media object.',
    maintainer='Eric Neuman',
    maintainer_email='eric@soloptimus.net',
    url="https://github.com/neuman/django-shannon",
    download_url = 'https://github.com/neuman/django-shannon/tarball/v1.0.3',
    install_requires=[
        'boto',
        'PIL',
        'youtube_dl'
    ],
    keywords=['django', 'media','s3','storage']
)