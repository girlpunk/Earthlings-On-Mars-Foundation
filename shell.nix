{ pkgs ? import <nixpkgs> {} }:
let
  editor-widgets = { python3, fetchurl }:
    with python3.pkgs;
    buildPythonApplication rec {
      pname = "django-editor-widgets";
      version = "1";

      src = pkgs.fetchFromGitHub {
        owner = "giorgi94";
        repo = "django-editor-widgets";
        rev = "7811e313e2087f50379d16da4aa7d0a08ccb55a4";
        hash = "sha256-0Jpgdty8pBSydIkcSyRS+vUz14Jn+d3pbcr+1S1p8FI=";
      };

      # By default tests are executed, but they need to be invoked differently for this package
      dontUseSetuptoolsCheck = true;
    };

  python = pkgs.python3.override {
    self = python;
    packageOverrides = final: prev: {
      django = final.django_5;
    };
  };
in
pkgs.mkShell {
  packages = [
    (python.withPackages( python-pkgs: with python-pkgs; [
      channels
      click
      daphne
      django_5
      lupa
      requests
    ]))
    (pkgs.callPackage editor-widgets {})
  ];
}
