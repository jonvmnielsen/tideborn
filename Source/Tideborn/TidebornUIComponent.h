#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornUIComponent.generated.h"

class UTidebornInventoryMenuWidget;
class UTidebornBuildMenuWidget;
class UTidebornCraftingComponent;
class UTidebornBuildComponent;
class UTidebornInventoryComponent;

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornUIComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornUIComponent();

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category="Tideborn|UI")
	void ToggleInventoryMenu();

	UFUNCTION(BlueprintCallable, Category="Tideborn|UI")
	void ToggleBuildMenu();

	UFUNCTION(BlueprintCallable, Category="Tideborn|UI")
	void CloseAllMenus();

	UFUNCTION(BlueprintCallable, Category="Tideborn|UI")
	void StartPlacingFoundation();

	UFUNCTION(BlueprintCallable, Category="Tideborn|UI")
	void CraftSelectedOrRecipe(FName RecipeId);

	UTidebornInventoryComponent* GetInventory() const;
	UTidebornCraftingComponent* GetCrafting() const;
	UTidebornBuildComponent* GetBuild() const;

	bool IsAnyMenuOpen() const;

private:
	UPROPERTY()
	TObjectPtr<UTidebornInventoryMenuWidget> InventoryMenu;

	UPROPERTY()
	TObjectPtr<UTidebornBuildMenuWidget> BuildMenu;

	void BindHotkeys();
	void OnInventoryKey();
	void OnBuildKey();
	void OnEscapeKey();
	void SetMenuMode(bool bMenuOpen);
};
