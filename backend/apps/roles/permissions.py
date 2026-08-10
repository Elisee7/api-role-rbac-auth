from rest_framework import permissions

class HasRolePermission(permissions.BasePermission):
    """
    Permission DRF réutilisable basée sur le rôle de l'utilisateur et les codes de permissions associées.
    """
    message = "Vous n'avez pas la permission requise pour effectuer cette action."

    def has_permission(self, request, view):
        # 1. Vérifier si l'utilisateur est connecté
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Les superutilisateurs (admins) contournent le contrôle de rôle
        if request.user.is_superuser:
            return True

        # 3. Récupérer la permission exigée par la vue (ex: required_permission = 'roles.manage')
        required_permission = getattr(view, 'required_permission', None)

        # Si la vue ne spécifie pas de permission requise, l'accès est accordé à tout utilisateur authentifié
        if not required_permission:
            return True

        # 4. L'utilisateur doit posséder un rôle
        if not request.user.role:
            self.message = "Aucun rôle n'est attribué à votre compte."
            return False

        # 5. Vérifier si le rôle possède le code de permission demandé
        has_perm = request.user.role.has_permission(required_permission)

        if not has_perm:
            self.message = f"Permission requise manquante : '{required_permission}'."

        return has_perm