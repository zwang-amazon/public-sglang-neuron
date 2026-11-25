# public-sglang-neuron (demo)

This repository is a working demo of a proposed development flow for SGLang-Neuron.
It stands in for the public `sgl-project/sglang-neuron` repository.
[`zwang-amazon/private-sglang-neuron`](https://github.com/zwang-amazon/private-sglang-neuron) (private)
stands in for the Neuron private development repository.

The Python package `sglang_neuron/` is synthetic. It exists only so that CI has something to test.
The scenario walkthrough and the mapping from each mechanism to the operating model are in [DEMO.md](DEMO.md).

## Role of this repository

- `main` is the only place code lands, through squash-merged pull requests.
- Every change follows the same steps, whoever wrote it: L0, review, L1 Trainium CI when hardware paths
  change, squash merge.
- Changes from Neuron's private repository arrive as ordinary pull requests, pushed by a push tool.
  Contributors open pull requests from forks.
- A sync bot in the private repository mirrors `main` there after each merge. Nothing flows back except
  through pull requests here.

## Rules on `main` (ruleset)

| Rule | Setting |
|---|---|
| Pull request required | Yes; required approvals are 0 in this demo because it has one maintainer account |
| Required checks | `L0` and `L1 Trainium gate` |
| Merge method | Squash only |
| Force push and deletion | Blocked |
| Bypass | None |

## CI

| Level | Workflow | Runs | Required |
|---|---|---|---|
| L0 | [`l0.yml`](.github/workflows/l0.yml): ruff, workflow lint, CPU unit tests, secret scan | Every pull request, including forks | Yes (`L0`) |
| L1 | [`l1-trainium.yml`](.github/workflows/l1-trainium.yml): smoke tests on a stub Trainium device | Pull requests that change `sglang_neuron/kernels/`; automatic for authors in [`CI_PERMISSIONS.json`](.github/CI_PERMISSIONS.json), otherwise after a maintainer approves the head commit | Through the gate |
| L1 gate | [`l1-gate.yml`](.github/workflows/l1-gate.yml): posts `L1 Trainium gate` | Every pull request | Yes (`L1 Trainium gate`) |
| L2 | Post-merge batch on internal CI, in the private repository | After each sync of `main` | No; results stay internal |

Maintainer approval for L1: comment `/tag-and-rerun-ci` or add the `run-ci` label. The approval applies to
the current head commit only, so a new push from an unlisted author needs a new approval.

## Contributing

1. Fork this repository and open a pull request against `main`.
2. L0 runs on your pull request.
3. If you change `sglang_neuron/kernels/` and are not in `CI_PERMISSIONS.json`, the `L1 Trainium gate`
   check stays pending until a maintainer reviews your commits and approves the Trainium run.
4. Fork pull requests run only public CI. They are never imported into the private repository.

## License

Apache-2.0. See [LICENSE](LICENSE).
