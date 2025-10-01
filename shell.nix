{pkgs ? import <nixpkgs> {}}: let
  python-ovr = pkgs.python3.override {
    self = pkgs.python3;
    packageOverrides = final: prev: {
      django = final.django_5;
    };
  };

  python-pkg = python-ovr.withPackages (python-pkgs:
    with python-pkgs; [
      channels
      click
      daphne
      django_5
      lupa
      pillow
      requests
    ]);

  editor-widgets = {
    python3,
    fetchurl,
  }:
    with python3.pkgs;
      buildPythonApplication rec {
        pname = "django-editor-widgets";
        version = "1";

        # https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/interpreters/python/mk-python-derivation.nix#L190
        format = "pyproject";
        nativeBuildInputs = [python-pkg];

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
in
  pkgs.mkShell {
    packages = [
      python-pkg
      (pkgs.callPackage editor-widgets {})
    ];
  }
