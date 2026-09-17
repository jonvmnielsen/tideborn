#include "TidebornUIComponent.h"
#include "TidebornMenuWidgets.h"
#include "TidebornInventoryComponent.h"
#include "TidebornCraftingComponent.h"
#include "TidebornBuildComponent.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/InputComponent.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "Engine/Engine.h"

UTidebornUIComponent::UTidebornUIComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UTidebornUIComponent::BeginPlay()
{
	Super::BeginPlay();

	if (APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr)
	{
		InventoryMenu = CreateWidget<UTidebornInventoryMenuWidget>(PC, UTidebornInventoryMenuWidget::StaticClass());
		BuildMenu = CreateWidget<UTidebornBuildMenuWidget>(PC, UTidebornBuildMenuWidget::StaticClass());
		if (InventoryMenu)
		{
			InventoryMenu->SetOwnerUI(this);
		}
		if (BuildMenu)
		{
			BuildMenu->SetOwnerUI(this);
		}
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornUIComponent::BindHotkeys));
	}
}

void UTidebornUIComponent::BindHotkeys()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC && GetWorld())
	{
		PC = GetWorld()->GetFirstPlayerController();
	}
	UInputComponent* IC = Pawn ? Pawn->InputComponent : nullptr;
	if (!IC && PC)
	{
		IC = PC->InputComponent;
	}
	if (!IC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornUIComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	IC->BindKey(EKeys::I, IE_Pressed, this, &UTidebornUIComponent::OnInventoryKey);
	IC->BindKey(EKeys::B, IE_Pressed, this, &UTidebornUIComponent::OnBuildKey);
	IC->BindKey(EKeys::Escape, IE_Pressed, this, &UTidebornUIComponent::OnEscapeKey);
	UE_LOG(LogTemp, Log, TEXT("TidebornUI: bound I/B/Esc"));
}

void UTidebornUIComponent::OnInventoryKey()
{
	ToggleInventoryMenu();
}

void UTidebornUIComponent::OnBuildKey()
{
	ToggleBuildMenu();
}

void UTidebornUIComponent::OnEscapeKey()
{
	if (UTidebornBuildComponent* Build = GetBuild())
	{
		if (Build->IsPlaceMode())
		{
			Build->CancelPlaceMode();
			return;
		}
	}
	CloseAllMenus();
}

bool UTidebornUIComponent::IsAnyMenuOpen() const
{
	return (InventoryMenu && InventoryMenu->IsInViewport()) || (BuildMenu && BuildMenu->IsInViewport());
}

void UTidebornUIComponent::SetMenuMode(bool bMenuOpen)
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PC)
	{
		return;
	}
	if (bMenuOpen)
	{
		FInputModeGameAndUI Mode;
		Mode.SetHideCursorDuringCapture(false);
		if (InventoryMenu && InventoryMenu->IsInViewport())
		{
			Mode.SetWidgetToFocus(InventoryMenu->TakeWidget());
		}
		else if (BuildMenu && BuildMenu->IsInViewport())
		{
			Mode.SetWidgetToFocus(BuildMenu->TakeWidget());
		}
		PC->SetInputMode(Mode);
		PC->bShowMouseCursor = true;
	}
	else
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->bShowMouseCursor = false;
	}
}

void UTidebornUIComponent::CloseAllMenus()
{
	if (InventoryMenu && InventoryMenu->IsInViewport())
	{
		InventoryMenu->RemoveFromParent();
	}
	if (BuildMenu && BuildMenu->IsInViewport())
	{
		BuildMenu->RemoveFromParent();
	}
	SetMenuMode(false);
}

void UTidebornUIComponent::ToggleInventoryMenu()
{
	if (!InventoryMenu)
	{
		return;
	}
	if (InventoryMenu->IsInViewport())
	{
		CloseAllMenus();
		return;
	}
	if (BuildMenu && BuildMenu->IsInViewport())
	{
		BuildMenu->RemoveFromParent();
	}
	if (UTidebornBuildComponent* Build = GetBuild())
	{
		Build->CancelPlaceMode();
	}
	InventoryMenu->Refresh();
	InventoryMenu->AddToViewport(50);
	SetMenuMode(true);
}

void UTidebornUIComponent::ToggleBuildMenu()
{
	if (!BuildMenu)
	{
		return;
	}
	if (BuildMenu->IsInViewport())
	{
		CloseAllMenus();
		return;
	}
	if (InventoryMenu && InventoryMenu->IsInViewport())
	{
		InventoryMenu->RemoveFromParent();
	}
	if (UTidebornBuildComponent* Build = GetBuild())
	{
		Build->CancelPlaceMode();
	}
	BuildMenu->Refresh();
	BuildMenu->AddToViewport(50);
	SetMenuMode(true);
}

void UTidebornUIComponent::StartPlacingFoundation()
{
	CloseAllMenus();
	if (UTidebornBuildComponent* Build = GetBuild())
	{
		Build->BeginPlaceMode(FName(TEXT("Foundation")));
	}
}

void UTidebornUIComponent::CraftSelectedOrRecipe(FName RecipeId)
{
	bool bOk = false;
	FString Feedback;
	if (UTidebornCraftingComponent* Craft = GetCrafting())
	{
		Craft->SelectRecipeById(RecipeId);
		bOk = Craft->TryCraft(RecipeId);
		if (bOk)
		{
			Feedback = FString::Printf(TEXT("Crafted %s — menu stays open"), *RecipeId.ToString());
		}
		else
		{
			Feedback = FString::Printf(TEXT("Need more materials for %s"), *RecipeId.ToString());
		}
	}
	// Brief juice inside the open menu — does not replace/close it
	NotifyCraftFeedback(Feedback, bOk);
	if (InventoryMenu && InventoryMenu->IsInViewport())
	{
		InventoryMenu->Refresh();
		InventoryMenu->ShowCraftFeedback(Feedback, bOk);
	}
	if (BuildMenu && BuildMenu->IsInViewport())
	{
		BuildMenu->Refresh();
	}
}

void UTidebornUIComponent::NotifyCraftFeedback(const FString& Message, bool bSuccess)
{
	if (GEngine && !Message.IsEmpty())
	{
		GEngine->AddOnScreenDebugMessage(92100, 2.5f, bSuccess ? FColor::Green : FColor::Orange, Message);
	}
}

UTidebornInventoryComponent* UTidebornUIComponent::GetInventory() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornInventoryComponent>() : nullptr;
}

UTidebornCraftingComponent* UTidebornUIComponent::GetCrafting() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornCraftingComponent>() : nullptr;
}

UTidebornBuildComponent* UTidebornUIComponent::GetBuild() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornBuildComponent>() : nullptr;
}
