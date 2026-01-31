# Homebrew formula for ixargs
# After releasing, update the version and sha256 below (run: shasum -a 256 ixargs-<version>.tar.gz)
# Replace REPO_OWNER with your GitHub username or org (e.g. beers)
# To update dependencies, run: python scripts/generate-formula-resources.py

class Ixargs < Formula
  include Language::Python::Virtualenv

  desc "Interactive xargs — run commands against stdin lines in a split-pane TUI"
  homepage "https://github.com/acbeers/ixargs"
  url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"

  depends_on "python@3.13"

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/38/71/3b932df36c1a044d397a1f92d1cf91ee0a503d91e470cbd670aa66b07ed0/markdown-it-py-3.0.0.tar.gz"
    sha256 "e3f60a94fa066dc52ec76661e37c851cb232d92f9886b15cb560aaada2df8feb"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/7c/2d/c3338d48ea6cc0feb8446d8e6937e1408088a72a39937982cc6111d17f84/pygments-2.18.0.tar.gz"
    sha256 "786ff802f32e91311bff3889f6e9a86e81505fe99f2735bb6d60ae0c5004f199"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/ab/3a/0316b28d0761c6734d6bc14e770d85506c986c85ffb239e688eeaab2c2bc/rich-13.9.4.tar.gz"
    sha256 "439594978a49a09530cff7ebc4b5c7103ef57baf48d5ea3184f21d9a2befa098"
  end

  resource "textual" do
    url "https://files.pythonhosted.org/packages/59/68/b6e4e93fd3b83ef3fcd7f04db993bb07ac4baa8ef9f6f7c0e2dfa08ab0de/textual-0.84.0.tar.gz"
    sha256 "2d512d2d39ce1b6e4f691dc6dc85d3a11854dcb223c02e6c8e83fa83c9e1bbbd"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/df/db/f35a00659bc03fec321ba8bce9420de607a1d37f8342eee1863174c69557/typing_extensions-4.12.2.tar.gz"
    sha256 "1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8"
  end

  def install
    virtualenv_install_with_resources
    man1.install "man/ixargs.1"
  end

  test do
    assert_match "usage", shell_output("#{bin}/ixargs --help 2>&1", 1)
  end
end
