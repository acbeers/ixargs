# Homebrew formula for ixargs
# After releasing, update the version and sha256 below (run: shasum -a 256 ixargs-<version>-darwin-arm64.tar.gz)
# Replace REPO_OWNER with your GitHub username or org (e.g. beers)

class Ixargs < Formula
  desc "Interactive xargs — run commands against stdin lines in a split-pane TUI"
  homepage "https://github.com/REPO_OWNER/ixargs"
  version "0.1.0"

  on_macos do
    on_arm do
      url "https://github.com/REPO_OWNER/ixargs/releases/download/v0.1.0/ixargs-0.1.0-darwin-arm64.tar.gz"
      # Update after release: shasum -a 256 <path-to-tarball>
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
    # Intel macOS: no pre-built binary; install with: pip install ixargs
  end

  def install
    # onedir tarball: ixargs/ contains executable + deps
    libexec.install "ixargs"
    bin.install_symlink libexec/"ixargs/ixargs"
  end

  test do
    assert_match "usage", shell_output("#{bin}/ixargs --help 2>&1", 1)
  end
end
