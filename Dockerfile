FROM nixos/nix
RUN nix-channel --remove nixpkgs &&\
    nix-channel --add https://nixos.org/channels/nixos-25.05 nixpkgs &&\
    nix-channel --update
RUN nix-build -A python3 '<nixpkgs>'

WORKDIR /app
COPY . .

EXPOSE 8000
#USER $APP_UID
ENTRYPOINT ["nix-shell", "--command", "./src/earthlings_on_mars_foundation/manage.py runserver 0.0.0.0:8000"]
