#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TidebornMenuWidgets.generated.h"

class UTidebornUIComponent;
class UVerticalBox;
class UTextBlock;
class UButton;

UCLASS()
class TIDEBORN_API UTidebornRecipeButtonWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(UTidebornUIComponent* InUI, FName InRecipeId, const FString& Label);

protected:
	virtual void NativeConstruct() override;

private:
	UPROPERTY()
	TObjectPtr<UTidebornUIComponent> OwnerUI;

	UPROPERTY()
	FName RecipeId;

	UPROPERTY()
	TObjectPtr<UButton> Button;

	UPROPERTY()
	TObjectPtr<UTextBlock> LabelText;

	FString PendingLabel;

	UFUNCTION()
	void HandleClick();
};

UCLASS()
class TIDEBORN_API UTidebornInventoryMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void SetOwnerUI(UTidebornUIComponent* InUI);
	void Refresh();

protected:
	virtual void NativeConstruct() override;

private:
	UPROPERTY()
	TObjectPtr<UTidebornUIComponent> OwnerUI;

	UPROPERTY()
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY()
	TObjectPtr<UTextBlock> BodyText;

	UPROPERTY()
	TObjectPtr<UVerticalBox> RecipeBox;

	UPROPERTY()
	TObjectPtr<UButton> CloseButton;

	UFUNCTION()
	void OnCloseClicked();
};

UCLASS()
class TIDEBORN_API UTidebornBuildMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void SetOwnerUI(UTidebornUIComponent* InUI);
	void Refresh();

protected:
	virtual void NativeConstruct() override;

private:
	UPROPERTY()
	TObjectPtr<UTidebornUIComponent> OwnerUI;

	UPROPERTY()
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY()
	TObjectPtr<UTextBlock> HelpText;

	UPROPERTY()
	TObjectPtr<UTextBlock> FoundationLabel;

	UPROPERTY()
	TObjectPtr<UButton> FoundationButton;

	UPROPERTY()
	TObjectPtr<UButton> CloseButton;

	UFUNCTION()
	void OnCloseClicked();

	UFUNCTION()
	void OnFoundationClicked();
};
