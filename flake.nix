{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/release-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              pythonPackagesOverlays =
                (prev.pythonPackagesOverlays or [])
                ++ [
                  (python-final: python-prev: {
                    django = python-final.django_5;
                  })
                ];

              python313 = let
                self = prev.python313.override {
                  inherit self;
                  packageOverrides = prev.lib.composeManyExtensions final.pythonPackagesOverlays;
                };
              in
                self;

              python313Packages = final.python313.pkgs;
            })
          ];
        };

        django-editor-widgets = {fetchurl}:
          pkgs.python313Packages.buildPythonPackage rec {
            name = "djangoeditorwidgets";

            nativeBuildInputs = with pkgs.python313Packages; [
              django
              pillow
              requests
            ];

            src = pkgs.fetchFromGitHub {
              owner = "giorgi94";
              repo = "django-editor-widgets";
              rev = "7811e313e2087f50379d16da4aa7d0a08ccb55a4";
              hash = "sha256-0Jpgdty8pBSydIkcSyRS+vUz14Jn+d3pbcr+1S1p8FI=";
            };
          };

        app = pkgs.python313Packages.buildPythonApplication rec {
          name = "earthlings_on_mars_foundation";
          src = ./.;
          format = "other";
          installPhase = ''
            mkdir -p $out/bin
            cp -r src/earthlings_on_mars_foundation $out
            makeWrapper ${pkgs.python313Packages.daphne}/bin/daphne $out/bin/app \
              --prefix PYTHONPATH : ${pkgs.python313Packages.makePythonPath propagatedBuildInputs} \
              --chdir "$out/earthlings_on_mars_foundation" \
              --run "${pkgs.python313}/bin/python manage.py migrate --no-input" \
              --run "${pkgs.python313}/bin/python manage.py collectstatic --no-input --link" \
              --add-flags "-b 0.0.0.0 earthlings_on_mars_foundation.asgi:application"
          '';

          propagatedBuildInputs = with pkgs.python313Packages; [
            (pkgs.callPackage django-editor-widgets {})
            channels
            click
            daphne
            django_5
            lupa
            pillow
            requests
            psycopg2
          ];
        };
      in
        with pkgs; rec {
          devShell = mkShell {
            packages = [
              app
            ];
          };

          packages.earthlings_on_mars_foundation = app;
          defaultPackage = packages.earthlings_on_mars_foundation;

          formatter = pkgs.alejandra;
        }
    );
}
