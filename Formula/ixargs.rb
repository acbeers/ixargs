# Homebrew formula for ixargs
# After releasing, update the version and sha256 below (run: shasum -a 256 ixargs-<version>.tar.gz)
# Replace acbeers with your GitHub username or org (e.g. beers)
# To update dependencies, run: python scripts/generate-formula-resources.py

class Ixargs < Formula
  include Language::Python::Virtualenv

  desc "Interactive xargs — run commands against stdin lines in a split-pane TUI"
  homepage "https://github.com/acbeers/ixargs"
  url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  license "MIT"

  depends_on "python@3.13"

  resource "markdown-it-py" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  resource "mdurl" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  resource "pygments" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  resource "rich" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  resource "textual" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  resource "typing-extensions" do
    url "https://github.com/acbeers/ixargs/releases/download/v0.1.0/ixargs-0.1.0.tar.gz"
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  end

  def install
    virtualenv_install_with_resources
    man1.install "man/ixargs.1"
  end

  test do
    assert_match "usage", shell_output("#{bin}/ixargs --help 2>&1", 1)
  end
end
