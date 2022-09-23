Docker installation guide
=================================================
The receipt-parser-server image gets built automatically using the `Docker Hub <https://hub.docker.com/r/disi33/receipt-parser>`_.
The installation is very simple. First pull the image from Docker hub.

.. code-block:: bash

    docker pull disi33/receipt-parser:latest
   

Recommended
"""""""""""""""

The launcher script does take care of various things e.g.

* cleanup old Docker container
* forward IP
* use the pseudo TTY
* forward configuration file

1. Download the launcher script
2. Execute the launcher script

.. code-block:: bash

    wget https://raw.githubusercontent.com/ReceiptManager/receipt-parser-server/master/util/launcher.sh
    wget https://raw.githubusercontent.com/ReceiptManager/receipt-parser-server/master/config.yml
    bash launcher.sh



Manual
"""""""""""""""
You could also run the Docker image without the launcher script e.g.

.. code-block:: bash

    docker run -i -t -p [YOUR-IP]:8721:8721  disi33/receipt-parser



Developer installation guide
=================================================

Clone the repository
"""""""""""""""""""""""""""""

First clone the GitHub project.

.. code-block:: bash

   git clone https://github.com/ReceiptManager/receipt-parser-server

Install project dependencies
"""""""""""""""""""""""""""""

Please notice that you install following packages with your favorite package manager:

    * python
    * python-pip
    * libmagickwand-dev
    * tesseract-ocr-all
    * libgl1-mesa-glx
    * libmagickwand-dev
    * qrencode

.. code-block:: bash

    apt-get install python python-pip libmagickwand-dev tesseract-ocr-all libgl1-mesa-glx libmagickwand-dev


Install python dependencies
""""""""""""""""""""""""""""""
Now, install all python dependencies using `pip` the following

.. code-block:: bash

    pip install -r requirements.txt

Generate SSL certificates
"""""""""""""""""""""""""""""""

Now, generate new SSL certificates. First, generate a new file called ``.private_key`` and type your favourite password. Please submit at least 8 characters. You can do this using echo like:

.. code-block:: bash

    echo "favorite_password" > .private_key

The password is used to generate the root certificate. Generate the cert files using

.. code-block:: bash

    make generate_cert

Now, you should see new certificates located in cert folder which is located in the root directory.

.. code-block:: bash

    ls cert

The output looks like the following

.. code-block:: text

    rootCA.key  rootCA.pem  rootCA.srl  server.crt  server.csr  server.csr.cnf  server.key  v3.ext


Run the server
"""""""""""""""""""""""""""""""
Now, you are ready to run the Receipt Parser Server.

.. code-block:: bash

    make serve

Verify installation
=================================================

If you run the Docker image. The output should like similar to:

.. code-block:: text

    ...
    INFO:     Started server process [16322]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on https://0.0.0.0:8721 (Press CTRL+C to quit)

The API token in printed on the screen. Additionally, you can scan the QR code.

.. code-block:: text

    Current API token: XXXXXXXX
