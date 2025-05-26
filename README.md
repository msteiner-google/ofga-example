## Preamble

This repo wants to showcase:

1. How to deploy a OpenFGA server + CloudSQL combo (`/terraform` directory)
2. How to configure it using python (they only have API access so look at the `/src/cli_commands` folder)
3. How to use it within an [ADK agent](https://google.github.io/adk-docs/) (`/src/agent` folder)

As a bonus, I would also love to convince you that this is a best practice and non trivial agents that need to
serve different content to different users should go with this (unless the use case is really really simple).

Finally, it might seem that this is a bit over-engineered (like, who uses dependency injection frameworks in python??), and you are right.
The reason is that I want to start using this as a template for agents going forward.

## Why OpenFGA and why Fine-grained ACLs?

The short answer is that while it is true that you can roll your own ACL system, chances are
it is gonna break soon. Requirements in this space are ever changing and having a system
that can handle everything is extremely hard.

One of the pre-built and open source tools is [OpenFGA](https://openfga.dev/) (Open Fine-Grained ACLs). It is a
project that is part of [The Linux Foundation](https://www.linuxfoundation.org/) and as
[March 2024](https://openfga.dev/blog/fine-grained-news-2024-03#cncf-incubation)
in the incubation stage of the CNCF. For these reasons I picked it while building this example, but there are
many other tools inspired by Google's [Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)

For more information I recommend going through the [docs](/docs) folder.

## Technical topics

### Setup

#### Python

The repo uses [uv](https://docs.astral.sh/uv/).

After having created a virtual environment with:

```
uv venv --python 3.12
```

and activated it with

```
source .venv/bin/activate
```

you can install all the dependencies with

```
uv sync --all-groups
```

Once that is done the python part is ready.
