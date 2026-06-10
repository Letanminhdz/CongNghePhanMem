#!/bin/bash
FRONTEND_DIR="/home/dazvo/Projects/www/CongNghePhanMem/frontend/public/Front-end"
PUBLIC_DIR="/home/dazvo/Projects/www/CongNghePhanMem/frontend/public"

declare -A FILE_MAP=(
    ["AdminOverviewDasboard.html"]="AdminDashboard.html"
    ["AI-Management.html"]="AdminAI.html"
    ["DiseaseManagement.html"]="AdminDiseases.html"
    ["MedicineManagement.html"]="AdminMedicines.html"
    ["Reports.html"]="AdminReports.html"
    ["UserManagement.html"]="AdminUsers.html"
    ["AI-ChatboxConsultation.html"]="chatbot.html"
    ["DrugInteractionChecker.html"]="InteractionChecker.html"
    ["Landingpage.html"]="index.html"
    ["DiseaseLookupPage.html"]="DiseaseLookup.html"
    ["MedicineLookupPage.html"]="MedicineLookup.html"
    ["UserDasboard.html"]="UserDashboard.html"
    ["DiseaseDetails.html"]="DiseaseDetails.html"
    ["MedicineDetails.html"]="MedicineDetails.html"
    ["ForgotPassword.html"]="ForgotPassword.html"
)

for src in "${!FILE_MAP[@]}"; do
    dest="${FILE_MAP[$src]}"
    if [ -f "$FRONTEND_DIR/$src" ]; then
        cp "$FRONTEND_DIR/$src" "$PUBLIC_DIR/$dest"
        echo "Copied $src to $dest"
    fi
done

# Copy new files directly
for new_file in "Edit Account.html" "Settings Account.html" "Settings General.html" "Log In.html" "Register.html"; do
    if [ -f "$FRONTEND_DIR/$new_file" ]; then
        cp "$FRONTEND_DIR/$new_file" "$PUBLIC_DIR/$new_file"
        echo "Copied new file $new_file"
    fi
done

