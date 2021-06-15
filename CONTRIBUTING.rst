=================
Development guide
=================

Architecture
============

The Edge SDK consists of a top-level ``click`` CLI wrapper and several
sub-commands for the various supported operations. For commands requiring
Ansible, there is an ``ansible`` module containing playbooks, roles, and some
additional wrappers that allow invoking Ansible from within Python directly.
Commands do not need to interface with Ansible and can perform any logic
required. More complicated commands should be pulled out into their own module,
which should export a "cli" function that provides the wrapper for the command
to ``click``.

Debugging Ansible playbooks
===========================

If you need to debug an Ansible playbook in more detail, you can invoke the
playbook via the SDK's own mechanism by running the ``chi_edge.ansible`` module::

  poetry run python -m chi_edge.ansible --help
