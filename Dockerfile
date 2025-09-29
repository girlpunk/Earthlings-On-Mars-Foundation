FROM nixos/nix
RUN nix-channel --remove nixpkgs &&\
    nix-channel --add https://nixos.org/channels/nixos-25.05 nixpkgs &&\
    nix-channel --update
RUN nix-build -A python3 '<nixpkgs>'

WORKDIR /app
COPY . .
RUN nix-shell --command "cd src/earthlings_on_mars_foundation; exit"

EXPOSE 8000
#USER $APP_UID
ENTRYPOINT ["nix-shell", "--command", "cd src/earthlings_on_mars_foundation; python manage.py migrate; daphne -b 0.0.0.0 earthlings_on_mars_foundation.asgi:application"]
