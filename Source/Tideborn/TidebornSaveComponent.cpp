#include "TidebornSaveComponent.h"
#include "TidebornSaveGame.h"
#include "TidebornInventoryComponent.h"
#include "TidebornBuildComponent.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Engine/World.h"

UTidebornSaveComponent::UTidebornSaveComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UTidebornSaveComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornSaveComponent::BindHotkeys));
	}
}

void UTidebornSaveComponent::BindHotkeys()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC && GetWorld())
	{
		PC = GetWorld()->GetFirstPlayerController();
	}
	if (!PC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornSaveComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	UInputComponent* IC = PC->InputComponent;
	if (!IC)
	{
		IC = Pawn ? Pawn->InputComponent : nullptr;
	}
	if (!IC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornSaveComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	IC->BindKey(EKeys::F5, IE_Pressed, this, &UTidebornSaveComponent::OnSaveKey);
	IC->BindKey(EKeys::F9, IE_Pressed, this, &UTidebornSaveComponent::OnLoadKey);
	UE_LOG(LogTemp, Log, TEXT("TidebornSave: bound F5/F9"));
}

void UTidebornSaveComponent::OnSaveKey()
{
	SaveCamp();
}

void UTidebornSaveComponent::OnLoadKey()
{
	LoadCamp();
}

bool UTidebornSaveComponent::SaveCamp()
{
	UTidebornSaveGame* Save = Cast<UTidebornSaveGame>(UGameplayStatics::CreateSaveGameObject(UTidebornSaveGame::StaticClass()));
	if (!Save || !GetOwner())
	{
		return false;
	}

	if (UTidebornInventoryComponent* Inv = GetOwner()->FindComponentByClass<UTidebornInventoryComponent>())
	{
		Save->InventorySlots = Inv->Slots;
	}
	if (UTidebornBuildComponent* Build = GetOwner()->FindComponentByClass<UTidebornBuildComponent>())
	{
		Save->BuiltPieces = Build->GetPlacedTransforms();
	}

	const bool bOk = UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, bOk ? FColor::Green : FColor::Red,
			bOk ? TEXT("Tideborn Camp saved (F5)") : TEXT("Tideborn Save failed"));
	}
	return bOk;
}

bool UTidebornSaveComponent::LoadCamp()
{
	if (!UGameplayStatics::DoesSaveGameExist(SlotName, 0))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Orange, TEXT("Tideborn: no save yet"));
		}
		return false;
	}

	UTidebornSaveGame* Save = Cast<UTidebornSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
	if (!Save || !GetOwner())
	{
		return false;
	}

	if (UTidebornInventoryComponent* Inv = GetOwner()->FindComponentByClass<UTidebornInventoryComponent>())
	{
		Inv->SetSlots(Save->InventorySlots);
	}
	if (UTidebornBuildComponent* Build = GetOwner()->FindComponentByClass<UTidebornBuildComponent>())
	{
		Build->RestorePlaced(Save->BuiltPieces);
	}

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Green, TEXT("Tideborn Camp loaded (F9)"));
	}
	return true;
}
