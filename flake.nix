{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/release-25.05";
    flake-utils.url = "github:numtide/flake-utils";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    treefmt-nix,
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

        django-editor-widgets = _:
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

        django-no-queryset-admin-actions = _:
          pkgs.python313Packages.buildPythonPackage rec {
            pname = "django-no-queryset-admin-actions";
            format = "pyproject";
            version = "1.2.0";

            nativeBuildInputs = with pkgs.python313Packages; [
              setuptools
              setuptools-scm
            ];

            propagatedBuildInputs = with pkgs.python313Packages; [django];

            src = pkgs.fetchPypi {
              pname = "django_no_queryset_admin_actions";
              inherit version;
              hash = "sha256-Ya0GZsZvzJMXXaODw9gKhhbknYWUh4MCNbMnoL23B7E=";
            };
          };

        pypi_iterators = _:
          pkgs.python313Packages.buildPythonPackage rec {
            pname = "iterators";
            format = "pyproject";
            version = "0.2.0";

            nativeBuildInputs = with pkgs.python313Packages; [
              setuptools
              setuptools-scm
            ];

            src = pkgs.fetchPypi {
              pname = "iterators";
              inherit version;
              hash = "sha256-6ZJ6HqHvCBgw/RUS85FoV8Nr1LNycoGabNKdD0RDG5c=";
            };
          };

        cartesia = _:
          pkgs.python313Packages.buildPythonPackage rec {
            pname = "cartesia";
            format = "pyproject";
            version = "2.0.9";

            nativeBuildInputs = with pkgs.python313Packages; [
              poetry-core
              setuptools
              setuptools-scm
            ];

            propagatedBuildInputs = with pkgs.python313Packages; [
              aiohttp
              audioop-lts
              httpx
              httpx-sse
              (pkgs.callPackage pypi_iterators {})
              pydantic
              pydantic-core
              pydub
              websockets
            ];

            src = pkgs.fetchPypi {
              pname = "cartesia";
              inherit version;
              hash = "sha256-6LdXsCoO8ij2EDF950qiKn8EfReFcVJ+zAaUItfBRjk=";
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
              --add-flags "-b 0.0.0.0 earthlings_on_mars_foundation.asgi:application"

            makeWrapper ${pkgs.python313}/bin/python $out/bin/manage \
              --prefix PYTHONPATH : ${pkgs.python313Packages.makePythonPath propagatedBuildInputs} \
              --chdir "$out/earthlings_on_mars_foundation" \
              --add-flags manage.py

            cd "$out/earthlings_on_mars_foundation"
            ${pkgs.python313}/bin/python manage.py collectstatic --no-input --link
          '';

          propagatedBuildInputs = with pkgs.python313Packages; [
            channels
            click
            daphne
            django_5
            django-health-check
            lupa
            pillow
            (pkgs.callPackage cartesia {})
            (pkgs.callPackage django-editor-widgets {})
            (pkgs.callPackage django-no-queryset-admin-actions {})
            psycopg2
            pyyaml
            requests
          ];
        };

        treefmt = treefmt-nix.lib.evalModule pkgs (
          {pkgs, ...}: {
            # Used to find the project root
            projectRootFile = "flake.nix";

            # Enable the Nix formatter
            programs.alejandra.enable = true;
            programs.statix.enable = true;

            # Enable the YAML formatter
            programs.yamlfmt.enable = true;
            settings.formatter.yamllint = {
              command = "${pkgs.yamllint}/bin/yamllint";
              includes = ["*.yaml" "*.yml"];
            };

            # Enable the Markdown formatter
            programs.mdformat.enable = true;

            # Enable the Lua formatter
            programs.stylua.enable = true;
            settings.formatter.selene = {
              command = "${pkgs.selene}/bin/selene";
              includes = ["*.lua"];
            };

            # Enable the Python formatters
            programs.ruff-format = {
              enable = true;
              lineLength = 180;
            };
            programs.ruff-check = {
              enable = true;
              extendSelect = [
                "A"
                "ANN"
                "ARG"
                "ASYNC"
                "B"
                "BLE"
                "C"
                "C4"
                "C90"
                "COM"
                "D"
                "DOC"
                "DTZ"
                "E"
                "EM"
                "EXE"
                "F"
                "F"
                "FA"
                "FBT"
                "FIX"
                "FLY"
                "FURB"
                "G"
                "I"
                "ICN"
                "INP"
                "INT"
                "ISC"
                "LOG"
                "N"
                "PERF"
                "PGH"
                "PIE"
                "PL"
                "PTH"
                "PYI"
                "Q"
                "Q"
                "RET"
                "RSE"
                "RUF"
                "S"
                "SIM"
                "SLF"
                "T10"
                "T20"
                "TC"
                "TD"
                "TID"
                "TRY"
                "UP"
                "W"
                "W"
                "YTT"
              ];
            };
          }
        );
      in
        with pkgs; rec {
          devShells.default = mkShell {
            packages = [
              app
            ];
          };

          apps.default = {
            type = "app";
            program = "${app}/bin/manage";
          };
          packages.default = app;
          packages.container = pkgs.dockerTools.buildImage {
            name = "ghcr.io/girlpunk/earthlings-on-mars-foundation";
            tag = "latest";

            config = {
              Cmd = ["${app}/bin/app"];
              Expose = [8000];
            };

            copyToRoot = with pkgs.dockerTools; [
              usrBinEnv
              binSh
              caCertificates
              fakeNss

              bash
              coreutils
            ];
          };

          formatter = treefmt.config.build.wrapper;
          checks = {
            formatting = treefmt.config.build.check self;
            django-check = pkgs.writeShellScript "django-check.sh" ''
              ${pkgs.python313}/bin/python src/earthlings_on_mars_foundation/manage.py check
            '';
            django-test = pkgs.writeShellScript "django-test.sh" ''
              ${pkgs.python313}/bin/python src/earthlings_on_mars_foundation/manage.py test
            '';
          };
        }
    );
}
