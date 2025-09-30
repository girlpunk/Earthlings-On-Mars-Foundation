{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/release-25.05";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:nix-community/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pyproject-nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python-ovr = pkgs.python3.override {
          self = pkgs.python3;
          packageOverrides = final: prev: {
            django = final.django_5;
          };
        };

        python-pkg = (python-ovr.withPackages( python-pkgs: with python-pkgs; [
            channels
            click
            daphne
            django_5
            lupa
            pillow
            requests
          ]));

        django-editor-widgets = { python3, fetchurl }:
          with python3.pkgs;
          buildPythonPackage rec {
            pname = "djangoeditorwidgets";
            version = "1";

            # https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/interpreters/python/mk-python-derivation.nix#L190
            format = "pyproject";
            nativeBuildInputs = [ python-pkg ];

            src = pkgs.fetchFromGitHub {
              owner = "giorgi94";
              repo = "django-editor-widgets";
              rev = "7811e313e2087f50379d16da4aa7d0a08ccb55a4";
              hash = "sha256-0Jpgdty8pBSydIkcSyRS+vUz14Jn+d3pbcr+1S1p8FI=";
            };

            # By default tests are executed, but they need to be invoked differently for this package
            doCheck = false;
            dontUseSetuptoolsCheck = true;
          };
      in with pkgs; rec {
        devShell = mkShell {
          packages = [
            python-pkg
            (pkgs.callPackage django-editor-widgets {})
          ];
        };

        # https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/interpreters/python/python-packages-base.nix
        # https://github.com/NixOS/nixpkgs/blob/master/pkgs/build-support/setup-hooks/make-wrapper.sh
        packages.app = python-ovr.pkgs.buildPythonApplication rec {
          name = "app";
          src = ./.;
          format = "other";
          installPhase = ''
            mkdir -p $out/bin
            cp -r src/earthlings_on_mars_foundation $out
            makeWrapper ${python-ovr.pkgs.daphne}/bin/daphne $out/bin/app \
              --prefix PYTHONPATH : ${python3Packages.makePythonPath propagatedBuildInputs} \
              --chdir "$out/earthlings_on_mars_foundation" \
              --add-flags "-b 0.0.0.0 earthlings_on_mars_foundation.asgi:application"
          '';
          propagatedBuildInputs = with python-ovr.pkgs; [
            (pkgs.callPackage django-editor-widgets {})
            channels
            click
            daphne
            django_5
            lupa
            pillow
            requests
          ];
        };

        defaultPackage = packages.app;
      }
    );
}
