# Testing botocove in a lab environment

* Acquire admin credentials for your organization management account. [1]

    ```
    aws sso login --profile sandbox-mgmt
    aws2-wrap --generatestdout --profile sandbox-gmt --outprofile default
    ```

* Log into any account with a VPC and launch an EC2 instance:

    * with 16GB of RAM [2]
    * running Ubuntu Linux 20.04 [3]

* SSH into the instance.

    ```
    ssh -i ... ubuntu@...
    ```

* Paste the credentials into the instance config.

    ```
    vim ~/.aws/credentials
    ```

* Test that you have admin access to the organization management account.

    ```
    sudo apt update
    sudo apt install -y awscli
    aws sts get-caller-identity
    ```

* Install botocove's development tools.

    ```
    sudo apt install -y python3-pip
    pip3 install poetry
    export PATH="$PATH:$HOME/.local/bin"
    ```

* Clone the memory profiling branch.

    ```
    git clone --branch memory_profiling https://github.com/iainelder/botocove.git
    ```

* Install the development environment.

    ```
    cd botocove
    poetry install
    ```

* Run the profiling code on a single arbitrary member account to simulate an organization of 500.

    ```
    cd profiling
    poetry run python demo.py 644347852375 500
    ```

* End the SSH session.

* Retrieve the plot.

    ```
    scp -i ... ubuntu@...:/home/ubuntu/botocove/profiling/botocove_memory.png .
    ```


1. I can't launch EC2s in my organization management account because it lacks a VPC. I use AWS SSO to manage my access. aws2-wrap converts SSO credentials to the familiar format.
2. More memory than my desktop computer. The cheapest standard type is the r6g.large. The cheapest overall type is the x2gd.medium, but its use requires approval via a quota increase request.
3. Ubuntu Linux 20.04 ships with Python 3.8. It's the minimum version that botocove depends on.
